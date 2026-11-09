#!/usr/bin/env python3
"""One command that brings every copy of the ruleset up to date.

The rules live in one place and are copied into eight clients: the Hermes plugin, the Cursor
always-on rule, the opencode package, the DeepSeek Harness package, the two text exports, and the
installed plugin directory the running agent actually reads. Each copy had its own build step and its own way of going stale, which
is how a rule gets edited and never reaches the agent that needs it.

    python3 tools/update.py              # rebuild everything, install into the profile, verify
    python3 tools/update.py --bump 0.15.0  # same, and set that version in every manifest
    python3 tools/update.py --check      # change nothing; exit 1 if any copy is stale

The order matters and is fixed: rules first, then every generated copy, then the install, then the
checks. A failure at any step stops the run and names the copy that did not update.
"""
from __future__ import annotations

import argparse
import filecmp
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "i-have-autism"
RULES = ROOT / "hermes" / "rules.md"
PLUGIN_SRC = ROOT / "hermes"
PLUGIN_INSTALLED = Path.home() / ".hermes" / "profiles" / "ougi" / "plugins" / "i-have-autism"

MANIFESTS = (
    "package.json",
    "plugin.json",
    "gemini-extension.json",
    ".claude-plugin/plugin.json",
    ".codex-plugin/plugin.json",
    "hermes/plugin.yaml",
    "skills/i-have-autism/SKILL.md",
    "dsh/package.json",
)
VERSION_LINE = re.compile(r'("?version"?\s*:\s*"|version:\s*")[0-9][^"\n]*(")')

BUILDERS = (
    ("opencode package", [sys.executable, "tools/build_opencode_plugin.py"]),
    ("cursor always-on", [sys.executable, "cursor/build_always_on.py"]),
    ("rules text export", [sys.executable, "tools/export_rules_txt.py"]),
    ("system prompt export", [sys.executable, "tools/export_system_prompt_txt.py"]),
    ("dsh package", [sys.executable, "tools/build_dsh_plugin.py"]),
)

CHECKS = (
    ("opencode package", [sys.executable, "tools/build_opencode_plugin.py", "--check"]),
    ("cursor always-on", [sys.executable, "cursor/build_always_on.py", "--check"]),
    ("dsh package", [sys.executable, "tools/build_dsh_plugin.py", "--check"]),
)


def say(message: str) -> None:
    print(message, flush=True)


def run(step: str, command: list[str]) -> bool:
    result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
    if result.returncode == 0:
        say(f"  ok   {step}")
        return True
    say(f"  FAIL {step}")
    for line in (result.stdout + result.stderr).strip().splitlines()[-6:]:
        say(f"       {line}")
    return False


def current_version() -> str:
    import json

    return json.loads((ROOT / "package.json").read_text(encoding="utf-8"))["version"]


def bump(version: str) -> bool:
    """Set the version in every manifest that ships it, and nowhere else.

    The old version is not assumed: a previous run may have stopped halfway, leaving two versions in
    the tree. Any version string in a manifest is replaced, so the command is safe to repeat.
    """
    changed = []
    for name in MANIFESTS:
        path = ROOT / name
        if not path.exists():
            say(f"  skip {name}: нет файла")
            continue
        text = path.read_text(encoding="utf-8")
        new, count = VERSION_LINE.subn(rf"\g<1>{version}\g<2>", text, count=1)
        if not count:
            say(f"  FAIL {name}: строки версии не нашлось")
            return False
        if new != text:
            path.write_text(new, encoding="utf-8")
            changed.append(name)
    say(f"  ok   версия {version}: обновлено файлов {len(changed)}")
    return True


def rules_length() -> int:
    sys.path.insert(0, str(ROOT))
    import hermes as plugin  # noqa: E402  the plugin package doubles as the renderer

    return len(plugin.render_rules())


def install() -> bool:
    """Copy the plugin and the scripts it shells out to into the live profile."""
    if not PLUGIN_INSTALLED.parent.exists():
        say(f"  skip install: нет {PLUGIN_INSTALLED.parent}")
        return True
    PLUGIN_INSTALLED.mkdir(parents=True, exist_ok=True)
    copied = 0
    for name in ("__init__.py", "rules.md", "plugin.yaml"):
        source = PLUGIN_SRC / name
        if not source.exists():
            continue
        target = PLUGIN_INSTALLED / name
        if target.exists() and filecmp.cmp(source, target, shallow=False):
            continue
        shutil.copy2(source, target)
        copied += 1
    for folder in ("scripts", "references"):
        source_dir = SKILL / folder
        if not source_dir.is_dir():
            continue
        target_dir = PLUGIN_INSTALLED / folder
        target_dir.mkdir(exist_ok=True)
        for source in sorted(source_dir.glob("*.py")):
            target = target_dir / source.name
            if target.exists() and filecmp.cmp(source, target, shallow=False):
                continue
            shutil.copy2(source, target)
            copied += 1
        for source in sorted(source_dir.glob("*.md")):
            target = target_dir / source.name
            if target.exists() and filecmp.cmp(source, target, shallow=False):
                continue
            shutil.copy2(source, target)
            copied += 1
    say(f"  ok   установлено: обновлено файлов {copied}" if copied else "  ok   установлено: всё совпадает")
    return True


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description="Rebuild and install every copy of the ruleset.")
    parser.add_argument("--bump", metavar="VERSION", help="set this version in every manifest first")
    parser.add_argument("--check", action="store_true", help="change nothing, fail on drift")
    args = parser.parse_args(argv)

    say(f"правило: {RULES.relative_to(ROOT)}; версия: {current_version()}")

    if args.check:
        ok = all(run(step, command) for step, command in CHECKS)
        length = rules_length()
        limit = 4000
        say(f"  {'ok  ' if length <= limit else 'FAIL'} длина отрендеренного правила: {length} / {limit}")
        if length > limit:
            ok = False
        ok = install_check() and ok
        return 0 if ok else 1

    if args.bump and not bump(args.bump):
        return 1

    for step, command in BUILDERS:
        if not run(step, command):
            return 1

    length = rules_length()
    if length > 4000:
        say(f"  FAIL правило длиннее потолка: {length} > 4000")
        return 1
    say(f"  ok   длина отрендеренного правила: {length} / 4000")

    if not install():
        return 1

    for step, command in CHECKS:
        if not run(step, command):
            return 1
    say("готово: все копии совпадают с hermes/rules.md")
    return 0


def install_check() -> bool:
    stale = []
    for name in ("__init__.py", "rules.md"):
        source = PLUGIN_SRC / name
        target = PLUGIN_INSTALLED / name
        if source.exists() and (not target.exists() or not filecmp.cmp(source, target, shallow=False)):
            stale.append(str(target))
    if stale:
        say("  FAIL установленная копия отстала: " + ", ".join(stale))
        return False
    say("  ok   установленная копия совпадает")
    return True


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
