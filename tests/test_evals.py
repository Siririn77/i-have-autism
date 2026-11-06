"""The eval suite must stay loadable: a broken case file would silently score nothing."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CASES = ROOT / "evals" / "cases.json"
RUNNER = ROOT / "evals" / "run_evals.py"
# Виды проверок читаются из самого раннера: список, который ведут руками, отстаёт от кода молча.
CHECK_TYPES = set(re.findall(r'kind == "(\w+)"', RUNNER.read_text(encoding="utf-8")))
if not CHECK_TYPES:
    raise AssertionError("в раннере не нашлось ни одного вида проверки")


class EvalCasesTest(unittest.TestCase):
    def setUp(self):
        self.cases = json.loads(CASES.read_text(encoding="utf-8"))

    def test_cases_are_a_non_empty_list(self):
        self.assertIsInstance(self.cases, list)
        self.assertGreaterEqual(len(self.cases), 10)

    def test_every_case_has_the_required_fields(self):
        for case in self.cases:
            for field in ("id", "rule", "prompt", "checks"):
                self.assertIn(field, case, f"{case.get('id', '?')} misses {field}")
            self.assertTrue(case["checks"], f"{case['id']} has no checks")

    def test_ids_are_unique(self):
        ids = [case["id"] for case in self.cases]
        self.assertEqual(len(ids), len(set(ids)), f"duplicate ids: {ids}")

    def test_check_types_are_known(self):
        for case in self.cases:
            for check in case["checks"]:
                self.assertIn(check["type"], CHECK_TYPES, f"{case['id']} has {check['type']}")
                self.assertTrue(check.get("patterns"), f"{case['id']} has an empty pattern list")
                self.assertTrue(check.get("label"), f"{case['id']} has an unlabeled check")

    def test_forbids_head_declares_its_window(self):
        for case in self.cases:
            for check in case["checks"]:
                if check["type"] == "forbids_head":
                    self.assertGreater(check.get("chars", 200), 0)

    def test_runner_is_importable_source(self):
        source = RUNNER.read_text(encoding="utf-8")
        compile(source, str(RUNNER), "exec")


if __name__ == "__main__":
    unittest.main()
