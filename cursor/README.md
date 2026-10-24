# Cursor rules — literal output, readable code

Four `.mdc` rule files for [Cursor](https://cursor.com/docs/rules), derived from the
[`i-have-autism`](../skills/i-have-autism/SKILL.md) skill. They make Cursor's **Agent / Chat** write and
explain literally, and — the point of this set — turn the editor into something you can **learn from
while you type the code yourself**.

## Install

Copy the rules into a project (per project) or into your Cursor user config (everywhere):

```bash
# per project
mkdir -p .cursor/rules
cp cursor/rules/*.mdc .cursor/rules/

# or globally, from the Cursor settings directory
```

Or use the installer:

```bash
bash cursor/install.sh /path/to/your/project
```

Then open **Customize → Rules** in Cursor to confirm they loaded.

## What each file does

| file | applies | what it changes |
|---|---|---|
| `00-say-what-you-mean.mdc` | always | Literal meaning, no idioms, implicit steps named, no social softeners, disagreement on the first line, no asserting what was not checked. |
| `01-explain-the-line.mdc` | always | **The hybrid rule.** When you are writing and Cursor completes, it says what the line does, flags the decisions hidden in a completion, and refuses to slip a branch past you. |
| `02-code-that-reads.mdc` | always | The code standard: readability, maintainability and correctness at once, with the conflict order stated; loud errors; comments that earn their place. |
| `learning-mode.mdc` | on request | **Ask for it explicitly** (`@learning-mode`). Turns the editor into a teacher: you write, it explains back, names the risk, and asks one question. |

Three files apply always; the fourth is manual so it does not lecture you while you are just working.

## Always on: the whole ruleset in one rule

Three of the files above apply always, but they are a **port** of the language and code layers. The complete
condensed ruleset lives in one more file, and it is generated rather than written:

```
hermes/rules.md                 ← the single source (the same text Hermes injects)
cursor/build_always_on.py       ← writes the rule
cursor/always-on/i-have-autism.mdc
```

`cursor/always-on/i-have-autism.mdc` has `alwaysApply: true`, so Cursor feeds it to **every** Agent/Chat
request, exactly like the hook does on the other clients. Unlike them it cannot be switched off at runtime,
because Cursor has no hook to read a flag file — so the switch is whether the file is installed:

```bash
bash cursor/install.sh /path/to/project --always   # add it
bash cursor/install.sh /path/to/project --remove   # take everything back out
bash cursor/install.sh /path/to/project            # the four rules, without it
```

Global instead of per project: open **Cursor Settings → Rules → User Rules** and paste the body of
`cursor/always-on/i-have-autism.mdc`. Cursor stores user rules in settings, not in a file, so no path is
offered here — inventing one would be a lie.

Do not edit the generated rule by hand. Change `hermes/rules.md`, then run:

```bash
python3 cursor/build_always_on.py           # rewrite
python3 cursor/build_always_on.py --check   # fail if the committed rule is stale (CI runs this)
```

The check exists because two hand-maintained copies of one ruleset drift, and the stale one is always the
one the model happens to read.

## The honest limitation

**These rules do not affect Cursor Tab** (the grey ghost text). Per Cursor's own documentation, rules
reach **Agent (Chat)** and do not touch Tab or other AI features.

So the setup is:

- **Tab** completes your typing fast, without the rules.
- **Agent / Chat** is where the explanation lives — ask it about the line after Tab places it, or use
  `@learning-mode` to run the teaching loop.

That split is the right one anyway: Tab is mechanical speed, the conversation is where you actually read.

## Where these come from

The rules are a port of the language and code layers of `i-have-autism`, which is measured against a
no-skill baseline in A/B runs — see [`evals/`](../evals/). This port has **not** been A/B measured in
Cursor; it is a faithful translation of the same rules into Cursor's format. Treat it as a starting point
and change it when it is wrong.
