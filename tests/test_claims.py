"""Rule 31: a number enters the text with work, journal, year and status.

The failure this guards against is narrow and real: the figure was right, the journal was wrong, and
every word-level check passed because the words were there. So the tests work at cell level — a missing
journal, a year written as words, a status invented on the spot.
"""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"

sys.path.insert(0, str(ROOT / "tools"))
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("claims", ROOT / "tools" / "claims.py")
claims = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(claims)  # type: ignore[union-attr]


class ClaimsTest(unittest.TestCase):
    def test_a_complete_ledger_passes(self):
        text = (FIXTURES / "claims-good.md").read_text(encoding="utf-8")
        self.assertEqual([], claims.check(text))

    def test_a_wrong_journal_row_still_passes_but_a_bad_cell_does_not(self):
        # The checker cannot know the journal is wrong; it can demand that a journal is named.
        text = (FIXTURES / "claims-good.md").read_text(encoding="utf-8")
        self.assertEqual([], claims.check(text.replace("Lancet Planetary Health", "PNAS")))

    def test_a_year_in_words_is_a_defect(self):
        text = (FIXTURES / "claims-good.md").read_text(encoding="utf-8")
        problems = claims.check(text.replace("| 2021 |", "| twenty twenty one |"))
        self.assertTrue(any("четыре цифры" in problem for problem in problems), problems)

    def test_an_invented_status_is_a_defect(self):
        text = (FIXTURES / "claims-good.md").read_text(encoding="utf-8")
        problems = claims.check(text.replace("| установлено |", "| точно |"))
        self.assertTrue(any("не из списка" in problem for problem in problems), problems)

    def test_a_missing_row_cell_is_named(self):
        text = (FIXTURES / "claims-good.md").read_text(encoding="utf-8")
        problems = claims.check(text.replace("| The Lancet |", "|  |"))
        self.assertTrue(any("пустая ячейка" in problem for problem in problems), problems)

    def test_no_table_at_all_is_not_a_pass(self):
        self.assertTrue(claims.check("# Реестр\n\nтекст без таблицы\n"))

    def test_the_command_exits_one_on_the_bad_fixture(self):
        result = subprocess.run(
            [sys.executable, "tools/claims.py", "tests/fixtures/claims-bad.md"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(1, result.returncode, result.stdout)


if __name__ == "__main__":
    unittest.main()
