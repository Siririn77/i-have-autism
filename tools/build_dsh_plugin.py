#!/usr/bin/env python3
"""Copy the condensed ruleset into the DeepSeek Harness package and verify its shape.

The DSH package ships `rules.md` next to `lib/index.js`, because the plugin reads
it at boot. That file is a copy of `hermes/rules.md`, the one condensed core that
every always-on client injects, and a copy is exactly the thing that drifts. So
this script owns the copy: it writes it, and `--check` fails when the two differ.

    python3 tools/build_dsh_plugin.py          # write dsh/rules.md
    python3 tools/build_dsh_plugin.py --check  # change nothing; exit 1 on drift
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hermes" / "rules.md"
TARGET = ROOT / "dsh" / "rules.md"
MANIFEST = ROOT / "dsh" / "package.json"
PATCH = ROOT / "dsh" / "cordis.patch.yml"


def drift() -> list[str]:
    """Return every reason the DSH package is not a faithful copy, in file order."""
    problems: list[str] = []
    if not SOURCE.is_file():
        return [f"missing source ruleset: {SOURCE}"]
    if not TARGET.is_file():
        return [f"missing copy: {TARGET}"]
    if SOURCE.read_bytes() != TARGET.read_bytes():
        problems.append(f"{TARGET} differs from {SOURCE}")

    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    patch_rel = manifest.get("dsh", {}).get("bundle", {}).get("patch")
    if patch_rel != "./cordis.patch.yml":
        problems.append(f"dsh.bundle.patch is {patch_rel!r}, expected './cordis.patch.yml'")
    if not (MANIFEST.parent / (patch_rel or "")).is_file():
        problems.append(f"bundle patch {patch_rel!r} does not exist")
    if "rules.md" not in manifest.get("files", []):
        problems.append("'rules.md' is missing from the package `files` list, so npm would drop it")
    if "i-have-autism-dsh" not in PATCH.read_text(encoding="utf-8"):
        problems.append("cordis.patch.yml does not name the plugin row 'i-have-autism-dsh'")
    return problems


def main(argv: list[str]) -> int:
    check = "--check" in argv
    if not check:
        TARGET.write_bytes(SOURCE.read_bytes())
        print(f"copied {SOURCE.relative_to(ROOT)} -> {TARGET.relative_to(ROOT)}")
    problems = drift()
    if problems:
        for problem in problems:
            print(f"FAIL {problem}")
        return 1
    print("dsh package current")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
