"""Rule 30: a check that has never failed is not a check.

The test does not inspect the checker's logic. It runs the same command a maintainer runs and asks it
to prove, per declared check, that the bad input is refused. A checker that cannot fail — or a manifest
that only carries good inputs — fails here.
"""
import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "tools" / "checks.json"


class TeethTest(unittest.TestCase):
    def run_tool(self, *args):
        return subprocess.run(
            [sys.executable, *args], cwd=ROOT, capture_output=True, text=True
        )

    def test_every_declared_check_fails_on_its_bad_input(self):
        result = self.run_tool("tools/check_teeth.py")
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_every_entry_has_both_inputs_and_a_reason(self):
        for entry in json.loads(MANIFEST.read_text(encoding="utf-8"))["checks"]:
            with self.subTest(entry=entry["name"]):
                self.assertTrue(entry.get("good"), "нет входа, который должен проходить")
                self.assertTrue(entry.get("bad"), "нет входа, который должен падать")
                self.assertGreater(len(entry.get("why", "")), 10, "нет причины, значит нет правила")

    def test_the_manifest_is_not_empty(self):
        entries = json.loads(MANIFEST.read_text(encoding="utf-8"))["checks"]
        self.assertGreaterEqual(len(entries), 2)


if __name__ == "__main__":
    unittest.main()
