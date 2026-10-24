#!/usr/bin/env python3
"""Export exactly what the clients inject into the system prompt — the full ruleset.

Three sizes of the same standard ship in this repository, and they are easy to
confuse:

  skills/i-have-autism/SKILL.md   the full ruleset, read on demand          ~30k chars
  hermes/rules.md                 the condensed section for a platform cap   ~3.8k chars
  (this file)                     the full ruleset as the hook injects it    ~30k chars

The hook and the opencode plugin do not summarise anything: they strip the
frontmatter and pass the whole body through. That body is what this export
contains, byte for byte, so it can be diffed against a client's prompt dump
instead of being trusted.

The opt-in banner is not included: it names a flag path that differs per
machine, and it is not part of the rules.

Usage:
    python3 tools/export_system_prompt_txt.py [output]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "i-have-autism-system-prompt-full.txt"
FULL = ROOT / "skills" / "i-have-autism" / "SKILL.md"

FRONTMATTER = re.compile(r"^---[^\S\r\n]*\r?\n[\s\S]*?\r?\n---[^\S\r\n]*(?:\r?\n|$)")


def injected_body() -> str:
    """The exact string the hook prints after its banner, and opencode injects.

    Kept identical to hooks/always-on.mjs and .opencode/plugins/i-have-autism.mjs:
    frontmatter removed, trailing blank lines removed, everything else intact.
    """
    text = FULL.read_text(encoding="utf-8")
    return FRONTMATTER.sub("", text).rstrip()


def build() -> str:
    body = injected_body()
    header = (
        "I HAVE AUTISM — FULL RULESET, AS INJECTED INTO THE SYSTEM PROMPT\n"
        "=================================================================\n\n"
        f"{len(body)} characters, {len(body.splitlines())} lines.\n\n"
        "This is the complete text, not the condensed 3,838-character section:\n"
        "the hook (Claude Code, Codex), the opencode plugin and the Pi extension\n"
        "pass the whole body through unchanged. Only the YAML frontmatter and the\n"
        "opt-in banner are removed — the banner names a per-machine flag path and\n"
        "carries no rules.\n\n"
        "Byte-identical to what the clients receive. Verified by\n"
        "tests/test_system_prompt_export.py against the hook's own output.\n\n"
        "Stop phrase: \"stop autism mode\" or \"normal mode\".\n\n"
        "-----------------------------------------------------------------\n\n"
    )
    return header + body + "\n"


def main(argv: list[str]) -> int:
    out = Path(argv[0]) if argv else DEFAULT_OUT
    text = build()
    out.write_text(text, encoding="utf-8")
    print(f"wrote {out} — {len(text)} chars, {len(text.splitlines())} lines")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
