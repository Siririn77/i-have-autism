#!/usr/bin/env python3
"""Run the behaviour evals: the same prompts with and without the always-on rules.

Usage: python3 evals/run_evals.py [--limit N] [--workers 3]

Reads the ruleset from hermes/rules.md — the compact text that clients actually inject —
and calls the model twice per case: once with a neutral system prompt, once with the rules.
Checks are deterministic pattern matches, so the score does not depend on a judge model.

Writes evals/report-<date>.json and prints a table. Exit code 1 when the rules arm scores
no better than the baseline, or when any case errors.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "evals" / "cases.json"
OUT_DIR = ROOT / "evals" / "runs"
RULES = ROOT / "hermes" / "rules.md"
BASELINE_PROMPT = "You are a helpful assistant. Answer the user's request."


def load_key() -> str:
    key = os.environ.get("OLLAMA_API_KEY")
    if key:
        return key
    env_file = Path(os.environ.get("HERMES_ENV", "/root/.hermes/profiles/ougi/.env"))
    for line in env_file.read_text(encoding="utf-8").splitlines():
        if line.startswith("OLLAMA_API_KEY="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit("OLLAMA_API_KEY not found in the environment or " + str(env_file))


def ask(model: str, key: str, system: str, prompt: str, max_tokens: int) -> str:
    """Ask once. The model spends tokens on reasoning before it writes, so an empty
    answer with finish_reason "length" means the budget ran out, not that the model
    refused: retry with twice the budget before calling it an error."""
    budget = max_tokens
    for _ in range(3):
        payload = {
            "model": model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0,
            "max_tokens": budget,
        }
        request = urllib.request.Request(
            "https://ollama.com/v1/chat/completions",
            data=json.dumps(payload).encode(),
            headers={"Authorization": "Bearer " + key, "Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=240) as response:
                data = json.load(response)
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as error:
            time.sleep(5)
            last_error = f"{type(error).__name__}: {error}"
            continue
        choice = data["choices"][0]
        content = choice["message"].get("content") or ""
        if content.strip():
            return content
        last_error = f"empty answer (finish_reason={choice.get('finish_reason')}, budget={budget})"
        budget *= 2
    raise RuntimeError(last_error)


def check(answer: str, rule: dict) -> tuple[bool, list[str]]:
    """Return (passed, failures). Every check must hold; a check is a plain pattern test."""
    failures: list[str] = []
    lowered = answer.lower()
    first_line = answer.strip().splitlines()[0] if answer.strip() else ""
    first_160 = answer.strip()[:160]

    for item in rule["checks"]:
        kind = item["type"]
        patterns = item["patterns"]
        if kind == "requires":
            hit = any(p.lower() in lowered for p in patterns)
        elif kind == "forbids":
            hit = not any(p.lower() in lowered for p in patterns)
        elif kind == "first_line_not":
            hit = not any(p.lower() in first_line.lower() for p in patterns)
        elif kind == "forbids_head":
            limit = item.get("chars", 200)
            hit = not any(p.lower() in answer[:limit].lower() for p in patterns)
        elif kind == "first_line_has":
            hit = any(p.lower() in first_160.lower() for p in patterns)
        else:
            raise ValueError(f"unknown check type: {kind}")
        if not hit:
            failures.append(item["label"])
    return (not failures, failures)


def run_arm(model: str, key: str, system: str, case: dict) -> dict:
    answer = ask(model, key, system, case["prompt"], case.get("max_tokens", 6000))
    passed, failures = check(answer, case)
    return {"passed": passed, "failures": failures, "answer": answer}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="deepseek-v4.1-flash:1017")
    parser.add_argument("--workers", type=int, default=3, help="max concurrent requests; keep it at 3")
    parser.add_argument("--limit", type=int, default=0, help="run only the first N cases")
    parser.add_argument("--id", default="", help="run only the case with this id")
    parser.add_argument("--repeat", type=int, default=3, help="samples per arm; the majority decides")
    args = parser.parse_args()

    cases = json.loads(CASES.read_text(encoding="utf-8"))
    if args.id:
        cases = [case for case in cases if case["id"] == args.id]
    if args.limit:
        cases = cases[: args.limit]
    rules = RULES.read_text(encoding="utf-8")
    key = load_key()

    jobs = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for case in cases:
            for sample in range(args.repeat):
                jobs.append((case, "baseline", sample, pool.submit(run_arm, args.model, key, BASELINE_PROMPT, case)))
                jobs.append((case, "rules", sample, pool.submit(run_arm, args.model, key, rules, case)))
        results = {}
        for case, arm, sample, future in jobs:
            try:
                results[(case["id"], arm, sample)] = future.result()
            except RuntimeError as error:
                results[(case["id"], arm, sample)] = {"passed": False, "failures": [f"error: {error}"], "answer": ""}

    rows = []
    for case in cases:
        row = {"id": case["id"], "rule": case["rule"]}
        for arm in ("baseline", "rules"):
            samples = [results[(case["id"], arm, s)] for s in range(args.repeat)]
            wins = sum(sample["passed"] for sample in samples)
            row[arm] = wins * 2 > args.repeat
            row[f"{arm}_rate"] = f"{wins}/{args.repeat}"
            row[f"{arm}_failures"] = samples[0]["failures"]
            row[f"{arm}_answer"] = samples[0]["answer"]
            row[f"{arm}_samples"] = [
                {"passed": s["passed"], "failures": s["failures"], "answer": s["answer"]} for s in samples
            ]
        rows.append(row)

    base_score = sum(r["baseline"] for r in rows)
    rules_score = sum(r["rules"] for r in rows)
    total = len(rows)
    errors = sum(
        1
        for r in rows
        for f in r["rules_failures"] + r["baseline_failures"]
        if f.startswith("error:")
    )

    print(f"{'case':30} {'rule':12} base  rules")
    for row in rows:
        print(f"{row['id']:30} {row['rule']:12} {'PASS' if row['baseline'] else 'fail':4}  {'PASS' if row['rules'] else 'fail'}")
    print(f"\nbaseline {base_score}/{total}   rules {rules_score}/{total}   delta {rules_score - base_score:+d}")

    report = {
        "when": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": args.model,
        "rules_chars": len(rules),
        "repeat": args.repeat,
        "total": total,
        "baseline_score": base_score,
        "rules_score": rules_score,
        "errors": errors,
        "rows": rows,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc)
    out = OUT_DIR / f"report-{stamp:%Y%m%d-%H%M%S}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report: {out}")

    if errors or rules_score <= base_score:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
