"""The DeepSeek Harness package: the copy stays faithful and the section really registers.

Two things are checked here, and both are checked with an input that must fail:

1. `dsh/rules.md` is a byte copy of the one condensed core. A drift check that
   has never seen a drifted file proves nothing, so `drift()` is fed a tree whose
   copy differs and must report it.
2. `apply()` registers exactly one prompt section whose text is the ruleset, with
   interpolation off. The negative controls are an empty ruleset, a missing file,
   and the documented off switch: each must produce no section, and the empty
   case must raise rather than register an empty string.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PKG = ROOT / "dsh"
NODE = shutil.which("node")


def run_plugin(pkg: Path, rules: Path | None = None, env: dict | None = None) -> dict:
    import os

    command = [NODE, str(ROOT / "tests" / "dsh_plugin_driver.mjs"), str(pkg)]
    if rules is not None:
        command.append(str(rules))
    # Both switches are read from the environment, and a shell that exported one
    # earlier would silently change what these tests measure: an inherited
    # I_HAVE_AUTISM_OFF=1 turns every positive case into "no section, no error".
    full_env = {**os.environ}
    for name in ("I_HAVE_AUTISM_OFF", "I_HAVE_AUTISM_RULES"):
        full_env.pop(name, None)
    full_env.update(env or {})
    result = subprocess.run(command, capture_output=True, text=True, env=full_env)
    if result.returncode != 0:
        raise AssertionError(f"driver failed: {result.stderr.strip()}")
    return json.loads(result.stdout)


@unittest.skipUnless(NODE, "node is not installed")
class DshPluginTest(unittest.TestCase):
    def test_registers_one_section_with_the_ruleset(self) -> None:
        rules = (ROOT / "hermes" / "rules.md").read_text(encoding="utf-8").strip()
        out = run_plugin(PKG)
        self.assertEqual(out["name"], "i-have-autism")
        self.assertEqual(out["inject"], ["systemPrompt"])
        self.assertEqual(out["sections"], 1, out)
        self.assertEqual(out["sectionName"], "i-have-autism")
        self.assertEqual(out["order"], 50)
        # The driver reports `interpolate === true`, so a literal section reads False here.
        self.assertFalse(out["interpolate"], "the section must be registered with interpolate: false")
        self.assertEqual(out["text"], rules)

    def test_empty_ruleset_fails_loudly(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            empty = Path(tmp) / "rules.md"
            empty.write_text("\n\n", encoding="utf-8")
            out = run_plugin(PKG, empty)
        self.assertEqual(out["sections"], 0)
        self.assertIn("is empty", out["error"] or "")

    def test_missing_ruleset_fails_loudly(self) -> None:
        out = run_plugin(PKG, Path("/nonexistent/rules.md"))
        self.assertEqual(out["sections"], 0)
        self.assertIn("ENOENT", out["error"] or "")

    def test_off_switch_registers_nothing(self) -> None:
        out = run_plugin(PKG, env={"I_HAVE_AUTISM_OFF": "1"})
        self.assertEqual(out["sections"], 0)
        self.assertIsNone(out["text"])


class DshPackageTest(unittest.TestCase):
    def test_rules_copy_is_current(self) -> None:
        result = subprocess.run(
            [sys.executable, "tools/build_dsh_plugin.py", "--check"],
            cwd=ROOT,
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("current", result.stdout)

    def test_drift_is_detected(self) -> None:
        """Feed the checker a package whose rules copy is one byte off."""
        sys.path.insert(0, str(ROOT / "tools"))
        import build_dsh_plugin as builder  # noqa: E402

        with tempfile.TemporaryDirectory() as tmp:
            pkg = Path(tmp) / "dsh"
            shutil.copytree(builder.TARGET.parent, pkg)
            (pkg / "rules.md").write_text("stale\n", encoding="utf-8")
            original_target = builder.TARGET
            builder.TARGET = pkg / "rules.md"
            try:
                problems = builder.drift()
            finally:
                builder.TARGET = original_target
        self.assertTrue(any("differs from" in p for p in problems), problems)

    def test_manifest_and_patch_agree(self) -> None:
        manifest = json.loads((PKG / "package.json").read_text(encoding="utf-8"))
        self.assertEqual(manifest["dsh"]["bundle"]["patch"], "./cordis.patch.yml")
        self.assertEqual(manifest["exports"]["."]["default"], "./lib/index.js")
        self.assertIn("rules.md", manifest["files"])
        patch = (PKG / "cordis.patch.yml").read_text(encoding="utf-8")
        self.assertIn("name: 'i-have-autism-dsh'", patch)
        self.assertIn("id: i-have-autism", patch)
        self.assertNotIn("disabled: true", patch)


if __name__ == "__main__":
    unittest.main()
