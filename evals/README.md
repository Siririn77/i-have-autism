# Evals — how to read this directory

Two controlled A/B runs live here. Every run has two arms, and the **only** difference between them is
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
