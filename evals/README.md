# Evals — how to read this directory

Three controlled A/B runs live here. Every run has two arms, and the **only** difference between them is
whether the agent was given the skill:

| arm | means | register |
|-----|-------|----------|
| **`without-skill`** | the agent worked **without** the skill | the model's default register — shaped for a general reader |
| **`with-skill`** | the agent read `SKILL.md` first and followed it | the register the skill defines — shaped for a reader who pays for every ambiguity |

**In plain terms, the question you are asking:** `without-skill` is the **neurotypical-shaped default** — the
register an LLM produces for an average reader without any instruction. `with-skill` is the
**autistic-shaped register** — literal-first, every implicit step named, no idioms, no social padding,
disagreement on the first line, and code held to readability, maintainability and correctness.

Both arms used the same model (`deepseek-v4.1-flash`), the same task text, and were told not to mention
the experiment. Nothing else differs.

---

## The two runs

### `language-2026-10-08/` — the writing, side by side

18 files: 9 tasks × 2 arms. **This is where you can read the two registers against each other.**
The clearest pair is `T9_without-skill.md` vs `T9_with-skill.md` — the same question ("explain a database
transaction to a non-expert"):

- **`T9_without-skill.md`** opens with an analogy: *"Imagine you're at an ATM and you transfer $100…"*
- **`T9_with-skill.md`** opens with the definition: *"A database transaction is a group of database changes
  treated as one single change: either all of them happen, or none of them happen."*

That is the whole difference in one pair. The **without-skill arm** reaches for a scenario the reader
must imagine; the **with-skill arm** states the fact literally and lets the scenario come later, if at
all.

See **[SIDE-BY-SIDE.md](SIDE-BY-SIDE.md)** for three pairs already lined up, with the differences marked.

Task index for this run:

| file stem | task |
|-----------|------|
| `T1_*` | explain the JavaScript event loop to a junior |
| `T2_*` | atomic write (temp+rename) vs `fsync` |
| `T3_*` | fix a crashing `parseConfig`, with a note |
| `T4_*` | `slugify(title)` + a note |
| `T5_*` | review a buggy `total(items)` |
| `T6_*` | explain `applyDelta` line by line |
| `T7_*` | rewrite an ugly `proc` for clarity |
| `T8_*` | respond to a request to wipe a production table |
| `T9_*` | explain a database transaction to a non-expert |

Full write-up: **[AB-report.md](AB-report.md)**.

### `quality-2026-10-08/` — the code, judged mechanically

The code-quality run. Here the interesting artifacts are the **post-mortems**, which only the with-skill arm
produced (`reviews/`, 5 files, 0 from without-skill):

| file stem | task | note |
|-----------|------|------|
| `Q1_*` | in-memory rate limiter | with-skill found a total bypass on a non-finite clock |
| `Q2_*` | refactor an ugly function, behaviour unchanged | tie on behaviour |
| `Q3_*` | fix a duplicated-fact table | tie — both fixed it the same way |
| `Q4_*` | `parseDuration(text)` | without-skill returns a silent `NaN`; with-skill throws |
| `Q6_*` | `Money` helper (integer cents) | with-skill found a silent overflow |
| `Q5_*` (report only) | explain what makes code maintainable | with-skill: 43 concrete points vs 16 |

Full write-up and the scoring script in that directory.

### `decomposition-2026-11-05/` — the rules as an executable test

The third run, and the first one that is a **suite instead of a pair of transcripts**. 13 prompts, each
probed with `--repeat 3`, each scored by pattern checks rather than by a judge model. `run_evals.py`
replayed them with and without `hermes/rules.md` — the 3881-character text clients actually inject.

**Result: without the rules 10/13, with the rules 13/13** (after sharpening; the pre-sharpening run was 12/13). The gap is concentrated, not spread:

| case | without | with | what it shows |
|---|---|---|---|
| `decomposition-huge` | 0/3 | 2/3 | a ten-part series gets a plan on disk, units and gates — instead of a table of contents |
| `plan-lines-are-checkable` | 0/3 | 3/3 | the plan names runnable commands and avoids "тщательно" / "при необходимости" |
| `post-mortem-before-handover` | 1/3 | 3/3 | the answer ends in reading its own diff as a stranger's, not in a checklist |

Three cases first landed at 2/3 **with** the rules and 3/3 without: `disagree-first-line`,
`scope-stays-scope`, `unknowns-are-marked`. The rules were sharpened instead of the number being hidden:
a verdict now has to precede the code sample, a one-shot script gets its two or three plan lines in the
reply with no file, and a missing input is requested in one direct sentence. Two of the three moved to
3/3; `scope-stays-scope` is still 2/3 in one sample — the model sometimes fixes the neighbouring defect
silently and believes the task is done. That is the next rule to sharpen, not a number to explain away.

Two cases also turned out to measure wording instead of behaviour — `unknowns-are-marked` looked for the
literal `[?]` while the model asked for the file in plain words. The check was rewritten to accept any
direct request, and both arms went to 3/3: the case is now a regression guard, not a gap.

`SCORE.md` has the full table; each case has `_without-rules.md` and `_with-rules.md` side by side, so
the difference is readable without trusting the score. Two traps this suite already hit — a token budget
too small reads as a failed rule, and one sample is noise — are documented in `decomposition-2026-11-05/SCORE.md`.

---

## Reading a filename

```
T9_without-skill.md    T9 = task 9,  without-skill = without the skill
T9_with-skill.md       T9 = task 9,  with-skill    = with the skill
Q1_with-skill.review.md               the post-mortem the skill requires
```

`without-skill` is always the arm **without** the skill. If you remember one thing, remember that.

---

## Why the names are `without-skill` / `with-skill` and not `neurotypical` / `autistic`

Because the experiment measures **one instruction package**, not human neurotype. The arms differ by a
skill file, so naming them after people would claim more than the data shows.

What the data does show: the default arm reaches for analogies, softeners and scene-setting, and the
with-skill arm does not. That is a difference in **register**, produced by a text file. It is reproducible,
and you can re-run it — that is all it claims.
