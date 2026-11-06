"""The packaged opencode plugin must behave like the in-repository one.

The point of the package is that it carries its own ruleset, so these tests run
the built file from a directory that has no `skills/` or `.opencode/command/`
above it. If the build ever starts depending on the repository layout again,
every test here fails while the repository plugin's tests keep passing.
"""
import json
import os
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / "tools" / "build_opencode_plugin.py"
PACKAGE_JS = ROOT / "dist" / "opencode-plugin" / "i-have-autism.js"
REPO_JS = ROOT / ".opencode" / "plugins" / "i-have-autism.mjs"
DRIVER = ROOT / "tests" / "opencode_plugin_driver.mjs"


@unittest.skipUnless(shutil.which("node"), "node is required for the OpenCode plugin")
class OpenCodePackageTest(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        base = Path(self.temp_dir.name)
        self.plugin = base / "isolated" / "i-have-autism.js"
        self.plugin.parent.mkdir(parents=True)
        shutil.copyfile(PACKAGE_JS, self.plugin)
        self.config_dir = base / "config"
        (self.config_dir / "opencode").mkdir(parents=True)

    def run_plugin(self, plugin, mode, env_extra=None):
        env = os.environ.copy()
        env["XDG_CONFIG_HOME"] = str(self.config_dir)
        env.pop("I_HAVE_AUTISM_ALWAYS", None)
        if env_extra:
            env.update(env_extra)
        return subprocess.run(
            ["node", str(DRIVER), str(plugin), mode],
            check=False,
            capture_output=True,
            text=True,
            env=env,
        )

    def opt_in(self):
        (self.config_dir / "opencode" / ".i-have-autism-always").touch()

    def test_built_package_is_current(self):
        result = subprocess.run(
            ["python3", str(BUILD), "--check"],
            check=False, capture_output=True, text=True, cwd=ROOT,
        )
        self.assertEqual(0, result.returncode, result.stdout + result.stderr)

    def test_runs_from_a_directory_without_the_repository(self):
        self.opt_in()
        result = self.run_plugin(self.plugin, "context")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertIn("AUTISM MODE ACTIVE (always-on)", result.stdout)

    def test_manifest_is_publishable(self):
        manifest = json.loads((ROOT / "dist" / "opencode-plugin" / "package.json").read_text(encoding="utf-8"))
        self.assertEqual("opencode-i-have-autism", manifest["name"])
        self.assertEqual("module", manifest["type"])
        self.assertEqual("i-have-autism.js", manifest["main"])
        self.assertIn("i-have-autism.js", manifest["files"])
        self.assertEqual(
            json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"],
            manifest["version"],
            "version mismatch: the package is stale, run python3 tools/build_opencode_plugin.py "
            "after bumping the version",
        )

    def test_injection_matches_the_repository_plugin(self):
        self.opt_in()
        packaged = self.run_plugin(self.plugin, "context")
        repository = self.run_plugin(REPO_JS, "context")
        self.assertEqual(0, packaged.returncode, packaged.stderr)
        self.assertEqual(0, repository.returncode, repository.stderr)
        self.assertEqual(repository.stdout, packaged.stdout)

    def test_v1_api_matches_v2_api(self):
        self.opt_in()
        v2 = self.run_plugin(self.plugin, "context").stdout
        v1 = self.run_plugin(self.plugin, "v1-context").stdout
        self.assertEqual(v2, v1)

    def test_silent_without_any_switch(self):
        result = self.run_plugin(self.plugin, "context")
        self.assertEqual("", result.stdout)

    def test_environment_variable_turns_injection_on(self):
        result = self.run_plugin(self.plugin, "context", {"I_HAVE_AUTISM_ALWAYS": "1"})
        self.assertIn("AUTISM MODE ACTIVE (always-on)", result.stdout)

    def test_registers_skill_and_command(self):
        skill = self.run_plugin(self.plugin, "skill")
        command = self.run_plugin(self.plugin, "command")
        self.assertEqual(0, skill.returncode, skill.stderr)
        self.assertEqual(0, command.returncode, command.stderr)
        self.assertEqual("i-have-autism", json.loads(skill.stdout)[0]["id"])
        self.assertEqual("i-have-autism", json.loads(command.stdout)[0]["name"])

    def test_ruleset_carries_no_frontmatter(self):
        self.opt_in()
        text = self.run_plugin(self.plugin, "context").stdout
        self.assertNotIn("name: i-have-autism", text)
        self.assertNotIn("description:", text[:200])

    def test_installer_round_trip(self):
        script = ROOT / "opencode" / "install.sh"
        project = Path(self.temp_dir.name) / "project"
        project.mkdir()
        env = os.environ.copy()
        env["XDG_CONFIG_HOME"] = str(self.config_dir)

        installed = subprocess.run(
            ["bash", str(script), "--project", str(project), "--always"],
            check=False, capture_output=True, text=True, env=env,
        )
        self.assertEqual(0, installed.returncode, installed.stderr)
        target = project / ".opencode" / "plugins" / "i-have-autism.js"
        self.assertTrue(target.exists())
        self.assertTrue((self.config_dir / "opencode" / ".i-have-autism-always").exists())

        removed = subprocess.run(
            ["bash", str(script), "--project", str(project), "--remove"],
            check=False, capture_output=True, text=True, env=env,
        )
        self.assertEqual(0, removed.returncode, removed.stderr)
        self.assertFalse(target.exists())
        self.assertFalse((self.config_dir / "opencode" / ".i-have-autism-always").exists())


    def test_package_carries_every_script_and_reference(self):
        """SKILL.md calls these files; a package without them is a rule with no tool."""
        skill_dir = ROOT / "skills" / "i-have-autism"
        package_dir = ROOT / "dist" / "opencode-plugin" / "skills" / "i-have-autism"
        for folder in ("scripts", "references"):
            for source in sorted((skill_dir / folder).glob("*")):
                if not source.is_file():
                    continue
                copy = package_dir / folder / source.name
                self.assertTrue(copy.exists(), f"{copy} отсутствует в пакете")
                self.assertEqual(copy.read_text(encoding="utf-8"), source.read_text(encoding="utf-8"))

if __name__ == "__main__":
    unittest.main()
