# opencode package

This directory installs the **packaged** plugin — a single self-contained file
generated from `skills/i-have-autism/SKILL.md` by `tools/build_opencode_plugin.py`.

The plugin inside the repository (`.opencode/plugins/i-have-autism.mjs`) reads
its ruleset from `skills/` and its command from `.opencode/command/`, so it only
works inside this tree. The packaged file embeds both texts, which is what makes
it installable anywhere: npm, a global plugin directory, or one project.

## Install

```bash
bash opencode/install.sh                              # global, always-on off
bash opencode/install.sh --always                     # global, always-on on
bash opencode/install.sh --project /path/to/project   # one project
bash opencode/install.sh --remove                     # take it all back
```

The script copies `dist/opencode-plugin/i-have-autism.js` to
`~/.config/opencode/plugins/` (or `<project>/.opencode/plugins/`), and with
`--always` creates `~/.config/opencode/.i-have-autism-always`.

## What the plugin registers

| Surface | Effect |
| --- | --- |
| skill | `i-have-autism`, loadable with `/skill:i-have-autism` |
| command | `/i-have-autism`, applies the ruleset for the rest of the session |
| hook | system-prompt injection, only while the flag file or `I_HAVE_AUTISM_ALWAYS` is set |

Both runtime APIs are covered: V2 through `setup()` and the session `context`
hook, V1 through `server()` and `experimental.chat.system.transform`. The
injected text is byte-identical to the repository plugin's — a test asserts it.

## Environment variable

The flag file is the normal switch. For CI or a one-off run:

```bash
I_HAVE_AUTISM_ALWAYS=1 opencode
```

## Publishing to npm

`dist/opencode-plugin/package.json` is a valid manifest for the name
`opencode-i-have-autism`. From that directory:

```bash
npm publish --access public
```

Then any user can add it without copying files:

```json
{ "plugin": ["opencode-i-have-autism"] }
```

Publishing is a separate decision: it needs an npm account and a token, neither
of which this repository holds.
