# i-have-autism

<p align="center">
  <strong>Literal, explicit, direct. And exacting about the code.</strong>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-green.svg" alt="License"></a>
</p>

A skill for your coding agent that says what it means, names what it would otherwise leave implied, and holds the code to beauty and correctness — not just to "it runs".

Sibling to [i-have-adhd](https://github.com/ayghri/i-have-adhd). Same idea, different mechanism. That one is about working memory and dopamine. This one is about ambiguity and literalism.

## Install

Copy and paste into your CLI prompt:

```text
Install the i-have-autism skill/plugin from https://github.com/REPLACE_USERNAME/i-have-autism, refer to the repo's AGENTS.md for instructions.
```

Or see [INSTALL.md](INSTALL.md) for the per-client paths.

## What it does

Two things, and they are one thing.

**The words.** Meaning is literal first. `spill the beans` arrives as beans, and the reader pays the translation on every sentence. So: no idioms, no metaphor where a literal sentence works. Every implicit step is written down, because **unstated is absent** — the gap you filled without noticing is the gap the reader falls into. Disagreement is stated on the first line, not wrapped in a question or a compliment. Social softeners are removed, because a softener placed on an instruction turns the instruction into nothing.

**The code.** The same reader reads the code. So code must be readable, commented only where it earns its place — and **beautiful and correct**, not merely working. Correct on the inputs the task never mentioned. An ugly solution that is obvious beats a pretty one that must be decoded. After the work: a green run, then a post-mortem that reads your own code as a stranger's.

## Before and after

<table>
<tr>
<td width="50%">

### Before

> Great question! Let's think about this. Your auth flow has a few moving pieces: the middleware, the token verification, and the cookie handling. Looking at `src/auth.ts`, the `verifyToken` function (around lines 42–58) seems to be using an older `jsonwebtoken` API. One approach would be to update the package and rewrite that function. After making the change, you'd want to run the tests to confirm nothing breaks. By the way, you might also want to look at your dependency versions overall. Hope this helps!

</td>

<td width="50%">

### After

> Edit `src/auth.ts:42` to update the token validation.
>
> 1. Open `src/auth.ts`
> 2. Replace `verifyToken` (lines 42–58) with the snippet below
> 3. Run `npm test -- auth.spec.ts`
>
> If step 3 exits with `401`, the header is missing — add `Authorization` and rerun.
> Next: paste the first failing line.

</td>
</tr>
</table>

## The difference from i-have-adhd

| | i-have-adhd | i-have-autism |
| --- | --- | --- |
| Core problem | Working memory, dopamine | Ambiguity, literalism |
| Lead rule | Next action first | Meaning is literal first |
| What is added | Steps, wins, time estimates | No idioms, no implicit steps, direct disagreement |
| Code | — | Readability, comments, beauty, correctness, post-mortem |

Both share the response shape (action first, numbered steps, no preamble). This one adds the language layer and the code layer.

## The parts

Full text in [SKILL.md](./skills/i-have-autism/SKILL.md).

- **Part 0 — Language.** Literal meaning, named implicit steps, one action per step, no social padding, direct disagreement, explicit names and errors, plain questions.
- **Beauty and correctness.** Correct beyond the happy path; beauty is meaning per unit of the reader's effort.
- **Part 1 — Code that reads.** 11 rules, from the reader's straight path to "the size of the task is the size of the edit".
- **Part 2 — Comments that earn their place.** 7 rules, including two lines in one voice and the four-question check.
- **Part 3 — The answer.** 10 rules for the shape of a reply.
- **Part 4 — Post-mortem.** Green run first, then read your own code as a stranger's; fix what you find, do not describe it.

## When it yields

Explaining in full, destructive actions, a debug spiral, real ambiguity, a rule that fights the task, a rule that fights the harness. And one refusal case: a genuinely harmful request gets the objection **before** the work, in three lines — what, who it hurts, what to do instead — and never a moralizing lecture.

## Credit

The response-shape rules (Part 3) are adapted from [i-have-adhd](https://github.com/ayghri/i-have-adhd) by Ayoub G. The language layer is built on the **double empathy problem** (Milton, 2012) and on reviews of communication in autistic adults (de Marchena et al., *Curr Psychiatry Rep*, 2025), which find strengths in structured language tasks and a preference for literal, explicit meaning.

## License

[MIT](LICENSE).
