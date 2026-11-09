# i-have-autism for DeepSeek Harness

An always-on system-prompt section for [DeepSeek Harness](https://github.com/deepseek-ai/deepseek-harness)
(`dsh`). The ruleset is present before the first token: no `/` command, no user turn, nothing in the
transcript.

## Install

```sh
# from a checkout of this repository
dsh plugin --profile headless add file:$PWD/dsh

# or, once published, by name
dsh plugin --profile headless add i-have-autism-dsh
```

Use the profile you actually run (`headless`, `web`, `sdk`, `acp`, or your own). Installing a package
whose `package.json` declares `dsh.bundle` also selects its patch layer, so no hand-editing of
`cordis.patch.yml` is needed.

Check what the profile will boot:

```sh
dsh --profile headless --dump-config | grep -A2 i-have-autism
```

## What it registers

One section in `ctx.systemPrompt`:

| field | value |
|---|---|
| `name` | `i-have-autism` |
| `order` | `50` — after the deployment persona prefix (`0`), before first-party guidance |
| `text` | `rules.md`, read at boot |
| `interpolate` | `false` — the rules are literal text, not a prompt template |

No tool, no permission change, no server, no session-log writer. Unloading the plugin removes the
section; Cordis disposes the registration.

## Turning it off

```sh
I_HAVE_AUTISM_OFF=1 dsh headless "run the tests"     # this run only
dsh plugin --profile headless remove i-have-autism-dsh   # permanently
```

`I_HAVE_AUTISM_RULES=/path/to/rules.md` swaps the ruleset for one run, which is how a project can carry
its own condensed variant.

## When the ruleset is missing

Harness loads plugin rows at boot and reports a failed one without stopping the session:

```text
dsh: warning: 1 entry did not activate
i-have-autism (i-have-autism-dsh): Error: ENOENT: no such file or directory, open '…/rules.md'
```

The session then runs with no rules at all — the plugin never registers a half-empty section. That is
the deliberate trade: a loud warning and no rules beats a silent prompt section that looks present.

## What it is not

- **Not the full skill.** `rules.md` is the condensed core that every always-on client injects — the
  same text Hermes renders into its prompt section, capped at 4 000 characters. The long form, with
  examples and the evaluation record, lives in [`skills/i-have-autism/SKILL.md`](../skills/i-have-autism/SKILL.md)
  and is not in this package.
- **Not a skill loader.** Harness has its own skill mechanism; this package only injects prompt text.
  If you want the skill read on demand instead of always, copy the skill directory into your profile's
  skill directory and skip this package.
- **Not measured on Harness.** The rule set was A/B-tested on other clients
  ([evidence](../README.md#evidence)); this port moves the same text into a section and has not been
  re-measured in `dsh`. Saying otherwise would be a claim without a run behind it.

## Files

| file | role |
|---|---|
| `lib/index.js` | the plugin: `name`, `inject`, `apply(ctx)` |
| `lib/index.d.ts` | types for the exported surface |
| `rules.md` | the ruleset, copied from `hermes/rules.md` by `tools/build_dsh_plugin.py` |
| `cordis.patch.yml` | the bundle patch: one `insert` row naming this package |

## How far this was verified

Run against `dsh` 0.2.2-rc.1 on Node 24, with a local Messages endpoint standing in for the model
(`tests/mock_anthropic.py`), because no DeepSeek key exists on the build host:

- the package installs with `dsh plugin --profile headless add file:…/dsh`, and the composed profile
  lists the row;
- the request body sent to the endpoint contains the ruleset — the section reaches the prompt, not just
  the plugin registry;
- `I_HAVE_AUTISM_OFF=1` removes it from the same request, and the turn still completes;
- deleting `rules.md` from the installed copy makes the entry fail to activate with the message shown
  above.

What is **not** verified: model behaviour under the rules, since the endpoint returned a fixed word. The
rule set's effect was measured on other clients, not here.
