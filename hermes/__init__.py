"""i-have-autism — the ruleset as a Hermes system-prompt section.

Hermes keeps the system prompt byte-stable across turns so the prefix cache stays
reusable, and deliberately routes plugin context into the user message. The
documented exception for durable guidance is `register_system_prompt_section`:
it is rendered once per session, before session metadata, and recovered from the
persisted prompt after a restart — so the rules cost no cache churn and do not
appear as a message in the transcript.

The section is capped at 4,000 characters. `rules.md` is the condensed ruleset
written for that budget; the full 648-line version stays in
`skills/i-have-autism/SKILL.md`, loaded on demand when the user invokes the skill.

Turning it off: the section is registered per session, so it cannot be switched
mid-session. Say "stop autism mode" and the model returns to its default style
for the rest of the turn; to remove the section entirely, disable the plugin
(`hermes plugins disable i-have-autism`) and start a new session.
"""

from __future__ import annotations

import logging
from pathlib import Path

logger = logging.getLogger(__name__)

SECTION_ID = "i-have-autism.rules"
RULES_MD = Path(__file__).resolve().parent / "rules.md"
MAX_CHARS = 4500


def render_rules(path: Path | None = None) -> str:
    """Return the ruleset body, stripped of frontmatter and surrounding blanks.

    Raises FileNotFoundError when the file is missing: a silent empty section
    would look like a working plugin that teaches the model nothing.
    """
    text = (path or RULES_MD).read_text(encoding="utf-8")
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            text = text[end + 4 :]
    return text.strip()


def register(ctx) -> None:
    try:
        rules = render_rules()
    except OSError as exc:
        logger.warning("i-have-autism: cannot read the ruleset: %s", exc)
        return

    if not rules:
        logger.warning("i-have-autism: ruleset is empty, section not registered")
        return

    ctx.register_system_prompt_section(
        SECTION_ID,
        rules,
        position="after_memory",
        max_chars=MAX_CHARS,
    )
