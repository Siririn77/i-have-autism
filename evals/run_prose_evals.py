#!/usr/bin/env python3
"""Prose evals: the same article, three arms, checks that can be decided without a judge.

Prose cannot be executed, so the checks are about the things prose can be wrong about in verifiable
ways: a number and its year, a forecast labelled as a forecast, a source named next to the figure,
and a range given where the range is the honest answer.

Usage: python3 evals/run_prose_evals.py [--repeat 1] [--arms none,graph,aggressive]
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_evals import ask, check, load_key  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "evals" / "prose_cases.json"
OUT_DIR = ROOT / "evals" / "runs"

ARMS = {
    "none": "You are a careful writer. Answer the user's request.",
    "graph": """You are a careful writer.

Before writing, build a short graph of the article: the questions it must answer, the nodes with an
anchor (which fact or source forces this node), typed edges between them, and the stop rule — every
question answered three ways, no new node without a new axis. Then write the article. Keep the graph to
a compact block above the text.""",
    "aggressive": """You are a careful writer.

Before writing, build a graph with absolute coverage: root questions, nodes with anchors, typed edges,
a coverage matrix of axes x sections with no empty cell (a cell names nodes or says "не относится" with
a reason), and a register of what you deliberately leave out. Then write the article, and make sure every
node is discharged by a paragraph. Put the graph, the matrix and the register above the text.""",
}


def run_arm(model: str, key: str, arm: str, case: dict) -> dict:
    answer = ask(model, key, ARMS[arm], case["prompt"], case.get("max_tokens", 12000))
    passed, failures = check(answer, case)
    return {"passed": passed, "failures": failures, "answer": answer}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="deepseek-v4.1-flash:1017")
    parser.add_argument("--repeat", type=int, default=1)
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--arms", default="")
    parser.add_argument("--max-tokens", type=int, default=0, help="override the case budget for every arm")
    args = parser.parse_args()

    cases = json.loads(CASES.read_text(encoding="utf-8"))
    if args.max_tokens:
        for case in cases:
            case["max_tokens"] = args.max_tokens
    key = load_key()
    names = [arm.strip() for arm in args.arms.split(",")] if args.arms else list(ARMS)

    results: dict[tuple, dict] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs = []
        for case in cases:
            for arm in names:
                for sample in range(args.repeat):
                    jobs.append((case["id"], arm, sample, pool.submit(run_arm, args.model, key, arm, case)))
        for case_id, arm, sample, future in jobs:
            try:
                results[(case_id, arm, sample)] = future.result()
            except RuntimeError as error:
                results[(case_id, arm, sample)] = {
                    "passed": False,
                    "failures": [f"error: {error}"],
                    "answer": "",
                }

    rows = []
    for case in cases:
        row = {"id": case["id"], "arms": {}}
        for arm in names:
            samples = [results[(case["id"], arm, s)] for s in range(args.repeat)]
            wins = sum(1 for sample in samples if sample["passed"])
            merged: list[str] = []
            for sample in samples:
                for failure in sample["failures"]:
                    if failure not in merged:
                        merged.append(failure)
            row["arms"][arm] = {
                "majority": wins * 2 > args.repeat,
                "rate": f"{wins}/{args.repeat}",
                "failed_checks": merged,
                "words": len(samples[0]["answer"].split()),
                "answer": samples[0]["answer"],
            }
        rows.append(row)

    print(f"{'case':16}" + "".join(f" {arm:12}" for arm in names))
    for row in rows:
        print(f"{row['id']:16}" + "".join(f" {row['arms'][arm]['rate']:12}" for arm in names))
        for arm in names:
            detail = row["arms"][arm]
            print(f"  {arm}: слов {detail['words']}, провалено проверок {len(detail['failed_checks'])}")
            for failure in detail["failed_checks"]:
                print(f"    - {failure}")

    report = {
        "when": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": args.model,
        "suite": "prose",
        "arms": ARMS,
        "rows": rows,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"prose-report-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report: {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
