#!/usr/bin/env python3
"""Code evals: does a graph before the code change the code — and does ultra mode change it more?

Three arms, same prompt, hidden tests:

  none        neutral system prompt
  graph       graph first: root questions, typed edges, anchors, stop rule
  ultra       graph first + a cloud per node + a fidelity bar whose kind is a test

The check is not a pattern match on prose: the answer's Python is written to disk and run against a
hidden unittest suite the model never sees. A pass means the code survives the edge cases — empty input,
duplicates, touching intervals, BOM, non-ASCII.

Usage: python3 evals/run_code_evals.py [--repeat 3] [--workers 3] [--id slugify]
"""
from __future__ import annotations

import argparse
import ast
import concurrent.futures
import json
import re
import subprocess
import sys
import tempfile
import textwrap
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from run_evals import ask, load_key  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "evals" / "code_cases.json"
OUT_DIR = ROOT / "evals" / "runs"

ARMS = {
    "none": "You are a helpful coding assistant. Answer the user's request.",
    "graph": """You are a coding assistant.

Before writing code, write the graph of the task as a short section — small, sized to the task (3-5 nodes for a one-liner):
root questions the code must answer, nodes with an anchor (what in the request forces this node),
typed edges (causes / contrasts / repeats / contradicts). No anchor, no node. Stop when every question
has three answers and a new node would need a new axis.

Then write the code. Every node you opened must be discharged by the code or by a test you name.""",
    "ultra": """You are a coding assistant.

Before writing code, write the graph of the task and expand every node.

Graph: root questions the code must answer; nodes with an anchor; typed edges (causes / contrasts /
repeats / contradicts). No anchor, no node.

For every node:
- a cloud of its parts: a core, three to nine elements, and an edge label that says what the relation
  means (включает / предшествует / вызывает / усиливает / противопоставлен / цена / пример / доказательство);
- a fidelity bar on exactly this line, with exactly one kind:
  `- планка: тест | годно: <named test, command or property that fails on a bad implementation> | не годно: <the sentence that sounds like proof and proves nothing>`

Then write the code. The hardest test from the bars must be in the answer as real code, not as prose.
Every node must be discharged by the code or by one of those tests."""
}


FENCE = re.compile(r"^```([a-zA-Z0-9_+.-]*)[ \t]*\n(.*?)^```[ \t]*$", re.DOTALL | re.MULTILINE)


TEST_MARKERS = ("import unittest", "import pytest", "from unittest", "def test_", "class Test")


def _parses(code: str) -> bool:
    try:
        ast.parse(code)
    except SyntaxError:
        return False
    return True


def extract_code(answer: str) -> str:
    """The solution block, and only a block that is Python.

    Three stands got this wrong in three ways. A graph drawn in ```text was read as code. Then, once an
    answer carried both a solution and the tests that prove it, the last block was the test suite. Then a
    fence with no language held the plan in prose, and prose was imported as the solution. The rule now:
    a candidate must parse as Python and must not look like a test; among those the longest wins.
    """
    blocks = FENCE.findall(answer)
    candidates = [
        body for language, body in blocks
        if language.lower() in ("python", "py", "python3", "") and _parses(body)
    ]
    solutions = [body for body in candidates if not any(marker in body for marker in TEST_MARKERS)]
    if solutions:
        return max(solutions, key=len)
    if candidates:
        return max(candidates, key=len)
    # Ни одного распознанного блока — значит кода нет. Отдать прозу значит импортировать рисунок
    # и объявить модель виноватой в своей же ошибке.
    lines = answer.splitlines()
    for index, line in enumerate(lines):
        if re.match(r"^(def |class |import |from )", line):
            return "\n".join(lines[index:])
    return ""


def run_tests(code: str, tests: str) -> dict:
    """Write the answer to disk and run the hidden suite. Only the interpreter decides."""
    with tempfile.TemporaryDirectory() as workdir:
        directory = Path(workdir)
        (directory / "solution.py").write_text(code, encoding="utf-8")
        (directory / "test_solution.py").write_text(tests, encoding="utf-8")
        try:
            completed = subprocess.run(
                [sys.executable, "-m", "unittest", "-v", "test_solution"],
                cwd=directory,
                capture_output=True,
                text=True,
                timeout=60,
                env={"PATH": "/usr/local/bin:/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"},
            )
        except subprocess.TimeoutExpired:
            return {"passed": False, "tests": 0, "detail": "timeout after 60 s"}
        output = completed.stdout + completed.stderr
        ran = re.search(r"Ran (\d+) tests?", output)
        outcomes = re.findall(r"^(test_\w+).*?\.\.\. (ok|FAIL|ERROR|skipped)", output, re.MULTILINE)
        ok = sum(1 for _, status in outcomes if status == "ok")
        return {
            "passed": completed.returncode == 0 and bool(ran),
            "tests": int(ran.group(1)) if ran else 0,
            "ok": ok,
            "partial": round(ok / len(outcomes), 3) if outcomes else 0.0,
            "detail": "" if completed.returncode == 0 else output.strip()[-400:],
        }


def run_arm(model: str, key: str, arm: str, case: dict) -> dict:
    answer = ask(model, key, ARMS[arm], case["prompt"], case.get("max_tokens", 6000))
    code = extract_code(answer)
    result = run_tests(code, case["tests"]) if code.strip() else {"passed": False, "tests": 0, "ok": 0, "partial": 0.0, "detail": "no code block"}
    lowered = answer.lower()
    result.update(
        {
            "answer": answer,
            "code": code,
            "code_lines": len(code.splitlines()),
            "truncated": answer.count("```") % 2 == 1,
            "graphed": any(
                marker in lowered
                for marker in ("mermaid", "# task graph", "task graph", "--causes-->", "--contrasts-->", "## ")
            ),
            "kpi": "планка" in lowered,
            "kpi_bars": lowered.count("годно:"),
        }
    )
    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="deepseek-v4.1-flash:1017")
    parser.add_argument("--workers", type=int, default=3)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--id", default="")
    parser.add_argument("--file", default=str(CASES), help="which case file to run")
    parser.add_argument("--arms", default="", help="comma-separated subset: none,graph,ultra")
    parser.add_argument("--max-tokens", type=int, default=0, help="override the case budget for every arm")
    args = parser.parse_args()

    cases = json.loads(Path(args.file).read_text(encoding="utf-8"))
    if args.id:
        cases = [case for case in cases if case["id"] == args.id]
    key = load_key()
    names = [arm.strip() for arm in args.arms.split(",")] if args.arms else list(ARMS)
    unknown = [arm for arm in names if arm not in ARMS]
    if unknown:
        raise SystemExit(f"unknown arms: {unknown}")

    jobs = []
    results = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        for case in cases:
            for arm in names:
                for sample in range(args.repeat):
                    jobs.append((case["id"], arm, sample, pool.submit(run_arm, args.model, key, arm, case)))
        for case_id, arm, sample, future in jobs:
            try:
                results[(case_id, arm, sample)] = future.result()
            except RuntimeError as error:
                results[(case_id, arm, sample)] = {
                    "passed": False, "tests": 0, "ok": 0, "partial": 0.0, "detail": f"error: {error}", "answer": "", "code": "",
                    "code_lines": 0, "truncated": False, "graphed": False, "kpi": False, "kpi_bars": 0,
                }

    rows = []
    for case in cases:
        row = {"id": case["id"], "arms": {}}
        for arm in names:
            samples = [results[(case["id"], arm, s)] for s in range(args.repeat)]
            wins = sum(1 for sample in samples if sample["passed"])
            row["arms"][arm] = {
                "majority": wins * 2 > args.repeat,
                "rate": f"{wins}/{args.repeat}",
                "graphed": sum(1 for s in samples if s["graphed"]) * 2 > args.repeat,
                "kpi": sum(1 for s in samples if s["kpi"]) * 2 > args.repeat,
                "kpi_bars": max(s["kpi_bars"] for s in samples),
                "code_lines": samples[0]["code_lines"],
                "partial": round(sum(s["partial"] for s in samples) / len(samples), 3),
                # Каждая проба, а не только первая: число должно восходить к тексту, который его дал.
                "samples": [
                    {
                        "passed": s["passed"],
                        "partial": s["partial"],
                        "graphed": s["graphed"],
                        "kpi": s["kpi"],
                        "kpi_bars": s["kpi_bars"],
                        "truncated": s.get("truncated", False),
                        "detail": s["detail"],
                        "answer": s["answer"],
                    }
                    for s in samples
                ],
                "detail": samples[0]["detail"],
                "answer": samples[0]["answer"],
                "code": samples[0]["code"],
            }
        rows.append(row)

    totals = {arm: sum(1 for row in rows if row["arms"][arm]["majority"]) for arm in names}
    print(f"{'case':18}" + "".join(f" {arm:12}" for arm in names))
    for row in rows:
        print(f"{row['id']:18}" + "".join(f" {row['arms'][arm]['rate']:12}" for arm in names))
    print("\nпроходят все тесты:" + "".join(f"  {arm} {totals[arm]}/{len(rows)}" for arm in names))
    for arm in names:
        mean = sum(row["arms"][arm]["partial"] for row in rows) / len(rows)
        print(f"  {arm}: доля пройденных тестов {mean:.2f}")
    for arm in names:
        graphed = sum(1 for row in rows if row["arms"][arm]["graphed"])
        print(f"  {arm}: граф в ответе {graphed}/{len(rows)}, планка "
              f"{sum(1 for row in rows if row['arms'][arm]['kpi'])}/{len(rows)} "
              f"(больше всего планок в одном ответе: {max(row['arms'][arm]['kpi_bars'] for row in rows)})")

    report = {
        "when": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "model": args.model,
        "repeat": args.repeat,
        "suite": "code",
        "arms": ARMS,
        "totals": totals,
        "rows": rows,
    }
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out = OUT_DIR / f"code-report-{datetime.now(timezone.utc):%Y%m%d-%H%M%S}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"report: {out}")
    errors = sum(
        1 for row in rows for arm in names if row["arms"][arm]["detail"].startswith("error:")
    )
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
