import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CURSOR = ROOT / "cursor"
ALWAYS_ON = CURSOR / "always-on" / "i-have-autism.mdc"


class CursorAlwaysOnTest(unittest.TestCase):
    def test_generated_rule_is_up_to_date_with_the_single_source(self):
        # Two hand-maintained copies of one ruleset drift silently; the build
        # script is the only writer, and --check is the drift alarm.
        result = subprocess.run(
            ["python3", str(CURSOR / "build_always_on.py"), "--check"],
            check=False,
            capture_output=True,
            text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)

    def test_always_on_rule_carries_valid_frontmatter(self):
        text = ALWAYS_ON.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
        self.assertIsNotNone(match, "rule must open with YAML frontmatter")
        front = match.group(1)
        self.assertIn("alwaysApply: true", front)
        self.assertIn("description:", front)

    def test_always_on_rule_stays_under_cursors_line_guidance(self):
        lines = ALWAYS_ON.read_text(encoding="utf-8").splitlines()
        self.assertLess(len(lines), 500)

    def test_body_comes_from_the_same_source_as_hermes(self):
        source = (ROOT / "hermes" / "rules.md").read_text(encoding="utf-8").strip()
        rule = ALWAYS_ON.read_text(encoding="utf-8")
        self.assertIn(source, rule)
        self.assertNotIn("name: i-have-autism", rule)


class CursorInstallerTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.project = Path(self.temp.name) / "project"
        self.project.mkdir()
        self.dest = self.project / ".cursor" / "rules"

    def run_installer(self, *args):
        return subprocess.run(
            ["bash", str(CURSOR / "install.sh"), str(self.project), *args],
            check=False,
            capture_output=True,
            text=True,
        )

    def shipped(self, folder):
        return sorted(p.name for p in (CURSOR / folder).glob("*.mdc"))

    def test_default_install_keeps_the_always_on_rule_out(self):
        result = self.run_installer()
        self.assertEqual(0, result.returncode, result.stderr)
        installed = sorted(p.name for p in self.dest.glob("*.mdc"))
        self.assertEqual(self.shipped("rules"), installed)
        self.assertNotIn(ALWAYS_ON.name, installed)
        self.assertIn("--always", result.stdout)

    def test_always_install_adds_exactly_one_rule(self):
        result = self.run_installer("--always")
        self.assertEqual(0, result.returncode, result.stderr)
        installed = sorted(p.name for p in self.dest.glob("*.mdc"))
        self.assertEqual(sorted(self.shipped("rules") + self.shipped("always-on")), installed)

    def test_remove_clears_both_sets(self):
        self.run_installer("--always")
        result = self.run_installer("--remove")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual([], sorted(p.name for p in self.dest.glob("*.mdc")))

    def test_unknown_option_fails_loudly(self):
        result = self.run_installer("--nope")
        self.assertEqual(2, result.returncode)
        self.assertIn("unknown option", result.stderr)


if __name__ == "__main__":
    unittest.main()
