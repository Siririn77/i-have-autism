import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "i-have-autism-rules.txt"


class ExportRulesTest(unittest.TestCase):
    def test_exported_txt_matches_a_fresh_build(self):
        # The txt is a generated artifact: a stale copy is worse than none,
        # because it looks authoritative and is read as the rules.
        before = EXPORT.read_text(encoding="utf-8")
        result = subprocess.run(
            ["python3", str(ROOT / "tools" / "export_rules_txt.py")],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, EXPORT.read_text(encoding="utf-8"))

    def test_export_contains_both_rulesets(self):
        text = EXPORT.read_text(encoding="utf-8")
        self.assertIn("PART 1 — THE FULL RULESET", text)
        self.assertIn("PART 2 — THE CONDENSED RULESET", text)
        self.assertIn("The single law", text)
        self.assertIn("Literal meaning first", text)

    def test_export_carries_no_markdown_emphasis(self):
        text = EXPORT.read_text(encoding="utf-8")
        self.assertNotIn("**", text)
        self.assertNotIn("```", text)


if __name__ == "__main__":
    unittest.main()
