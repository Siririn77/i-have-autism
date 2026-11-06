"""The update mechanism has one job: after it runs, no copy of the ruleset is stale.

The failure this guards against is not a broken build, it is a green build that skipped a client.
So the test runs the same command a maintainer runs and asks it to prove there is no drift.
"""
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UPDATE = ROOT / "tools" / "update.py"


class UpdateTest(unittest.TestCase):
    def test_there_is_no_drift_in_the_repository(self):
        result = subprocess.run(
            [sys.executable, str(UPDATE), "--check"],
            cwd=ROOT, capture_output=True, text=True,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_the_mechanism_refuses_to_skip_a_client(self):
        # Every client that embeds the ruleset has a --check command of its own; the update script
        # must run them all, not the first one that passes.
        text = UPDATE.read_text(encoding="utf-8")
        self.assertIn("tools/build_opencode_plugin.py", text)
        self.assertIn("cursor/build_always_on.py", text)
        self.assertIn("plugins", text)

    def test_install_target_is_named_in_one_place(self):
        text = UPDATE.read_text(encoding="utf-8")
        self.assertEqual(1, text.count('"profiles"'), "the install path must not be duplicated")
