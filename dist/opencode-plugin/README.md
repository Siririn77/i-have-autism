# opencode-i-have-autism

An opencode plugin that installs the **i-have-autism** ruleset: literal meaning,
every implicit step named, no social padding, direct disagreement, and code held
to correctness, readability and maintainability.

Generated from `skills/i-have-autism/SKILL.md`, version 0.9.0.

## Install

Into the global plugin directory (one file, no dependencies):

```bash
mkdir -p ~/.config/opencode/plugins
cp i-have-autism.js ~/.config/opencode/plugins/
```

For one project only:

```bash
mkdir -p .opencode/plugins
cp i-have-autism.js .opencode/plugins/
```

From npm, once published:

```json
{ "plugin": ["opencode-i-have-autism"] }
```

## What it registers

- the `i-have-autism` skill, so `/skill:i-have-autism` loads the ruleset on demand;
- the `/i-have-autism` command, which applies the ruleset for the rest of the session;
- an **opt-in** always-on hook that puts the ruleset into the system prompt on
  every request without touching the visible conversation.

## Always on

Off by default. Turn it on with the flag file:

```bash
touch ~/.config/opencode/.i-have-autism-always
```

or for one process:

```bash
I_HAVE_AUTISM_ALWAYS=1 opencode
```

Turn it off for good by deleting the flag and unsetting the variable. Inside a
session, `stop autism mode` or `normal mode` suspends the rules for that session.
