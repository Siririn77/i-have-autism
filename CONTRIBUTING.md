# Contributing

This repository takes pull requests, issues, forks, and translations. Read the manifesto in
[README.md](README.md#manifesto--change-this-it-is-yours-now) first — it states the intent. This file
states the mechanics.

## The three ways to help, in order of value

1. **A measured failure.** An A/B run, a before/after pair, or a failing case showing a rule subtracting on
   an axis it claims to improve. This is the most valuable contribution and the one that needs no argument
   for inclusion — it arrives with its own evidence.
2. **A rule that is missing or wrong.** Name the rule, show the case it fails on, propose the wording.
3. **A translation or a new platform manifest.** Both extend reach without changing the rules.

## What a pull request must contain

- **One change per pull request.** Do not bundle a rule fix with a typo fix — the second makes the first
  harder to review.
- **The rule it touches, named.** `Part 1, rule 8 — Consistency beats taste`, not "improved the readability
  section".
- **What it costs.** Every rule costs something. State what yours costs, rather than claiming it is free.
- **A verification.** A before/after example, a failing test case, or a measured run. "It reads better" is
  not a verification.
- **The register of the skill itself.** Literal, direct, no preamble, no closing pleasantry. Hold this file
  to the standard the skill sets. A pull request that opens with "Great project!" is asking for a rewrite
  before review.

## What will be declined

- **A style change that trades correctness.** Correctness is the floor; the other axes are pursued inside
  it. This is not negotiable and is stated in the skill's own core.
- **A rule with no observable consequence.** A rule that cannot be falsified cannot be improved or removed;
  it can only be argued about. Every rule must produce a case where its absence is visible.
- **A rule that judges the person rather than the artifact.** The skill criticizes the code and the writing.
  It does not criticize the coder.
- **A restatement of a rule that already exists elsewhere.** The package has one home per rule; a duplicate
  is a defect, not a contribution.

## Running the verification

There is no build. The skill is markdown and the manifests are JSON. To check a change:

```bash
# every manifest is valid JSON
for f in plugin.json .claude-plugin/plugin.json .codex-plugin/plugin.json gemini-extension.json; do
  python3 -c "import json,sys; json.load(open('$f'))" && echo "ok $f"
done

# the root manifest validates against the Agent Plugins schema (requires: pip install jsonschema)
curl -sL https://agent-plugins.org/schemas/1.0.0/plugin.schema.json -o /tmp/plugin.schema.json
python3 -c "
import json, jsonschema
jsonschema.validate(json.load(open('plugin.json')), json.load(open('/tmp/plugin.schema.json')))
print('schema: ok')
"

# the skill frontmatter: name matches its directory, description under the cap
python3 -c "
import re
src = open('skills/i-have-autism/SKILL.md', encoding='utf-8').read()
fm = re.match(r'^---\n(.*?)\n---\n', src, re.S).group(1)
print('name ok:', re.search(r'^name:\s*(\S+)', fm, re.M).group(1) == 'i-have-autism')
"

# no Cyrillic anywhere — the repo is English-only (the skill's own language layer)
grep -rlP '[\x{0400}-\x{04FF}]' . --exclude-dir=.git && echo 'FOUND: translate it' || echo 'no Cyrillic: ok'
```

## Adding a rule to the skill

A rule is not live until it appears in **every** place a reader can reach it:

1. The rule itself, in its Part, with a `Bad:` / `Good:` pair.
2. The **checklist before you call it done**, under the right axis (readability, maintainability, or
   correctness).
3. If it is a load-bearing idea: the **two load-bearing rules** section, or the pillar section.
4. The README's **The parts** list, if it changes the shape of a section.

A rule wired into one place and missed in the others exists and does nothing — it will be skipped and never
reported as skipped.

## Version bumps

Any content change bumps `version` in **five** places, kept identical:

- `plugin.json`
- `.claude-plugin/plugin.json`
- `.codex-plugin/plugin.json`
- `gemini-extension.json`
- `skills/i-have-autism/SKILL.md` (frontmatter `metadata.version`)

A version line that disagrees across these means a client will load an older rule set than the repository
shows.

## License

By contributing, you agree your contribution is released under the repository's MIT license.
