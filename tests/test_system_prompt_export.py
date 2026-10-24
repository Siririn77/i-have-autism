import os
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXPORT = ROOT / "i-have-autism-system-prompt-full.txt"


@unittest.skipUnless(shutil.which("node"), "node is required to run the hook")
class SystemPromptExportTest(unittest.TestCase):
    def test_export_is_byte_identical_to_the_hook_body(self):
        # The claim on the tin is "this is what the client receives". Proving it
        # against the real hook beats re-implementing the stripping twice.
        with tempfile.TemporaryDirectory() as tmp:
            config = Path(tmp) / "claude"
            config.mkdir()
            (config / ".i-have-autism-always").touch()
            env = os.environ.copy()
            env["CLAUDE_CONFIG_DIR"] = str(config)
            result = subprocess.run(
                ["node", str(ROOT / "hooks" / "always-on.mjs")],
                check=False, capture_output=True, text=True, env=env,
            )
            self.assertEqual(0, result.returncode, result.stderr)

        printed = result.stdout
        first_blank = printed.find("\n\n")
        hook_body = printed[first_blank + 2 :]

        export = EXPORT.read_text(encoding="utf-8")
        marker = "-----------------------------------------------------------------\n\n"
        export_body = export.split(marker, 1)[1]

        self.assertEqual(hook_body, export_body)

    def test_export_matches_a_fresh_build(self):
        before = EXPORT.read_text(encoding="utf-8")
        result = subprocess.run(
            ["python3", str(ROOT / "tools" / "export_system_prompt_txt.py")],
            check=False, capture_output=True, text=True,
        )
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual(before, EXPORT.read_text(encoding="utf-8"))

    def test_export_holds_the_whole_ruleset(self):
        text = EXPORT.read_text(encoding="utf-8")
        for marker in ("Part 0. Language", "Part 1. Code that reads", "post-mortem",
                       "Pre-send check", "When the rules yield"):
            self.assertIn(marker, text)
        self.assertNotIn("name: i-have-autism", text)
        self.assertGreater(len(text), 30000)


if __name__ == "__main__":
    unittest.main()
