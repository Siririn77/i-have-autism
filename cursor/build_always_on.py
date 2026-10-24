#!/usr/bin/env python3
"""Generate the always-on Cursor rule from the single ruleset source.

`hermes/rules.md` is the condensed ruleset written for a 4,000-character
budget: it is the same text Hermes puts in its system-prompt section. Cursor
has no runtime hook, so its always-on path is a rule file with
`alwaysApply: true`; that file is generated here rather than copied by hand,
because two hand-maintained copies of one ruleset drift and nobody notices
which one is stale.

Usage:
    python3 cursor/build_always_on.py           # write the file
    python3 cursor/build_always_on.py --check   # fail if it is out of date
"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "hermes" / "rules.md"
TARGET = ROOT / "cursor" / "always-on" / "i-have-autism.mdc"

HEADER = """---
description: The i-have-autism ruleset, applied to every Agent/Chat request. Literal meaning, every implicit step named, no social padding, direct disagreement, code held to readability and correctness.
alwaysApply: true
---

<!-- Generated from hermes/rules.md by cursor/build_always_on.py. Do not edit by hand. -->
"""


def render() -> str:
    body = SOURCE.read_text(encoding="utf-8").strip()
    return HEADER + "\n" + body + "\n"


def main(argv: list[str]) -> int:
    expected = render()

    if "--check" in argv:
        actual = TARGET.read_text(encoding="utf-8") if TARGET.exists() else ""
        if actual != expected:
            print(f"{TARGET} is out of date: run python3 cursor/build_always_on.py", file=sys.stderr)
            return 1
        print(f"{TARGET.name} matches {SOURCE.name}")
        return 0

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(expected, encoding="utf-8")
    print(f"wrote {TARGET} ({len(expected)} chars, {len(expected.splitlines())} lines)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
