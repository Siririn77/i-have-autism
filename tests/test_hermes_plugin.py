import importlib.util
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_DIR = ROOT / "hermes"


def load_plugin():
    spec = importlib.util.spec_from_file_location(
        "i_have_autism_hermes", PLUGIN_DIR / "__init__.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeCtx:
    """Records the section instead of touching a live prompt."""

    def __init__(self):
        self.sections = []

    def register_system_prompt_section(self, section_id, content, **kwargs):
        self.sections.append((section_id, content, kwargs))


class HermesPluginTest(unittest.TestCase):
    def setUp(self):
        self.plugin = load_plugin()

    def test_registers_one_section_with_the_documented_contract(self):
        ctx = FakeCtx()
        self.plugin.register(ctx)

        self.assertEqual(1, len(ctx.sections))
        section_id, content, kwargs = ctx.sections[0]
        self.assertEqual("i-have-autism.rules", section_id)
        self.assertEqual("after_memory", kwargs["position"])
        self.assertEqual(4500, kwargs["max_chars"])
        self.assertTrue(content.strip())

    def test_section_fits_the_hard_limit_including_an_audit_heading(self):
        # Hermes caps a section at 4500 chars and adds its own audit heading
        # around plugin content, so the body must not fill the budget exactly.
        body = self.plugin.render_rules()
        self.assertLessEqual(len(body), 4500 - 100)

    def test_section_carries_the_load_bearing_rules(self):
        body = self.plugin.render_rules()
        for marker in ("Literal meaning", "unstated is absent", "KISS", "DRY", "reviews/"):
            self.assertIn(marker, body)

    def test_body_has_no_frontmatter(self):
        body = self.plugin.render_rules()
        self.assertFalse(body.startswith("---"))
        self.assertNotIn("name: i-have-autism", body)

    def test_missing_rules_file_registers_nothing_and_does_not_raise(self):
        ctx = FakeCtx()
        original = self.plugin.RULES_MD
        self.plugin.RULES_MD = PLUGIN_DIR / "does-not-exist.md"
        try:
            self.plugin.register(ctx)
        finally:
            self.plugin.RULES_MD = original
        self.assertEqual([], ctx.sections)

    def test_manifest_matches_the_package(self):
        manifest = (PLUGIN_DIR / "plugin.yaml").read_text(encoding="utf-8")
        self.assertIn("name: i-have-autism", manifest)
        package = json.loads((ROOT / "package.json").read_text(encoding="utf-8"))
        self.assertIn(f'version: "{package["version"]}"', manifest)


if __name__ == "__main__":
    unittest.main()
