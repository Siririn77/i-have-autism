# Install

The package follows two open standards, so one tree serves many clients:

- **Agent Plugins 1.0.0** — the distribution format (`plugin.json` at the root, skills under `skills/`).
  Read directly by Claude Code, Cursor, Codex (ChatGPT), VS Code, GitHub Copilot, and Hermes Agent.
- **Agent Skills** — the file format inside the package (`skills/i-have-autism/SKILL.md`).

Client-specific manifests are included in the tree for the clients that want their own:

| Client | Manifest |
| --- | --- |
| Agent Plugins (standard) | `plugin.json` |
| Claude Code | `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` |
| Codex | `.codex-plugin/plugin.json`, `.agents/plugins/marketplace.json` |
| Gemini CLI | `gemini-extension.json`, `GEMINI.md` |
| opencode | `.opencode/command/i-have-autism.md` (command) |

---

## Claude Code

From a local folder, for one session:

```bash
claude --plugin-dir /path/to/i-have-autism
```

As a personal plugin, permanently — add this repository as a marketplace, then install:

```bash
claude plugin marketplace add REPLACE_USERNAME/i-have-autism
claude plugin install i-have-autism@i-have-autism
```

The skill is invoked namespaced: `/i-have-autism:i-have-autism`.

## Cursor

Reads Agent Plugins and Agent Skills. Copy the skill to Cursor's skill directory:

```bash
mkdir -p ~/.cursor/skills
cp -r skills/i-have-autism ~/.cursor/skills/
```

Or point Cursor at the plugin via **Customize → Plugins**.

## Codex (ChatGPT)

Reads Agent Plugins. Add the repository as a plugin source per Codex's plugin settings, or copy the skill
into the skills directory the client scans.

## VS Code, GitHub Copilot

Both read Agent Plugins. Add the plugin through the client's plugin settings.

## opencode

**opencode does not read Agent Plugins.** Its "plugin" is a JavaScript module wired to events — a skill
package is the wrong format. opencode *does* read skills, from several locations. Copy the skill itself:

```bash
mkdir -p ~/.config/opencode/skills
cp -r skills/i-have-autism ~/.config/opencode/skills/
```

opencode finds `~/.config/opencode/skills/i-have-autism/SKILL.md` and loads it on demand. Project-scoped
alternative: `.opencode/skills/`. It also reads `~/.claude/skills/` and `~/.agents/skills/`.

The bundled `.opencode/command/i-have-autism.md` adds a `/i-have-autism` command that switches the rules on
for the session.

## Gemini CLI

The repository ships `gemini-extension.json` and `GEMINI.md`. Install as a Gemini CLI extension, or copy the
skill into the extension's skills path.

## Hermes Agent

Reads Agent Plugins. See the Hermes plugin documentation, or install the skill directly into the profile's
skills directory.

## Any other client

If it reads Agent Plugins → use the package root. If it reads Agent Skills → copy `skills/i-have-autism/`
into the skills directory it scans. The rules live in one file: `skills/i-have-autism/SKILL.md`.

## Turn it off

The rules persist for the whole session. Say **"stop autism mode"** or **"normal mode"** to return to the
default style.
