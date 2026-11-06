"""Rule 32 has to be measurable, not merely stated.

A report that opens with results and mentions the failure in passing reads like a success, and that is
exactly what happened once: three checks were read as a model failure and reported before the token
ceiling was mentioned. The `before` check makes the order itself the assertion.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "evals"))

import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("run_evals", ROOT / "evals" / "run_evals.py")
run_evals = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(run_evals)  # type: ignore[union-attr]


class BeforeTest(unittest.TestCase):
    rule = {
        "checks": [
            {
                "type": "before",
                "patterns": ["упал", "не хватило"],
                "after": ["прошли", "получилось"],
                "label": "сначала провал",
            }
        ]
    }

    def test_failure_first_passes(self):
        answer = "Три задачи упали: не хватило бюджета. Остальные семь прошли."
        self.assertEqual((True, []), run_evals.check(answer, self.rule))

    def test_success_first_fails(self):
        answer = "Семь задач прошли. Три упали из-за бюджета."
        passed, failures = run_evals.check(answer, self.rule)
        self.assertFalse(passed)
        self.assertEqual(["сначала провал"], failures)

    def test_no_failure_mentioned_is_not_a_pass(self):
        answer = "Все десять прошли, получилось отлично."
        self.assertFalse(run_evals.check(answer, self.rule)[0])

    def test_the_case_exists_and_is_wired(self):
        cases = json.loads((ROOT / "evals" / "cases.json").read_text(encoding="utf-8"))
        case = next(c for c in cases if c["id"] == "report-failure-first")
        self.assertEqual("32", case["rule"])


if __name__ == "__main__":
    unittest.main()
