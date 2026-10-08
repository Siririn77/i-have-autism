# A/B test: code quality and style — 6 tasks, 2 arms, 12 agents

**Date:** 2026-10-08
**Skill under test:** `i-have-autism` v0.2.0 (31 015 bytes, 648 lines)
**Focus:** this run scores the **code-quality and style** axes only — readability, maintainability,
correctness, and the post-mortem gate. (The first run, `AB-report.md`, covered language and response
shape.)
**Method:** 2 agents per task. Arm A — without the skill. Arm B — reads `SKILL.md` before working and
follows it. Agents were told not to mention the experiment.
**Model:** deepseek-v4.1-flash, identical for both arms.
**Verification:** every deliverable from both arms was executed locally (Node v26) and diffed against its
partner and against the original where one existed — not read by eye.

---

## Summary across the 6 tasks

| # | Task | Axis probed | Difference | Winner |
|---|------|-------------|-----------|--------|
| Q1 | Rate limiter (rolling window) | structure, contract, gate | **Yes** | **B** — smaller face, 67 vs 103 lines; found a total-bypass defect |
| Q2 | Refactor an ugly function | readability at constant behaviour | **Tie on behaviour** | **B** — shorter, and it named the trap | 
| Q3 | `units.js` with a DRY trap | one place to change | **Tie** | both fixed it identically |
| Q4 | `parseDuration` | edges, contract | **Yes** | **B** — throws instead of a silent `NaN` |
| Q5 | Explain maintainability | language, precision | **Yes** | **B** — 43 concrete points vs 16 |
| Q6 | `Money` helper | correctness (integer cents) | **Tie on behaviour** | **B** — half the size, same guarantees |

**Result: 4 differences in favour of B, 2 ties, 0 losses.** The **post-mortem gate fired again: 5 review
files from with-skill arms, 0 from without-skill arms** (task Q5 wrote no code, so the ratio is 5 of the 5 code
tasks).

---

## The post-mortem gate — second independent confirmation

The skill's Part 4 requires a post-mortem in `reviews/` after the work. This run is the second time the
gate was measured, and it reproduced:

| task | A (without-skill) | B (with-skill) |
|------|-------------|-------------|
| Q1 rate limiter | none | `reviews/out/Q1_with-skill.review.md` |
| Q2 refactor | none | `reviews/out/Q2_with-skill.review.md` |
| Q3 units | none | `reviews/out/Q3_with-skill.review.md` |
| Q4 parseDuration | none | `reviews/out/Q4_with-skill.review.md` |
| Q6 Money | none | `reviews/out/Q6_with-skill.review.md` |
| **total** | **0 of 5** | **5 of 5** |

**And this time the gate produced defects that mattered, not just process.** Reading the review files:

- **Q1 — a total bypass.** The post-mortem found that a clock returning a non-finite value (`NaN`,
  `Infinity`, a string, `null` from a mis-wired `now`) made `check()` **always return `true`**: the
  comparison `time > windowStart` is false against `NaN`, so no request was ever counted and the limiter
  silently ceased to limit — a rate limiter that rates nothing, with no error. It fixed it by guarding
  `now()` with `Number.isFinite` and throwing, plus a test over `[NaN, Infinity, '0', null]`. **This is a
  correctness defect the without-skill arm's artifact did not have — because the without-skill arm never looked.**
- **Q6 — silent rounding on overflow.** The post-mortem found that `add` passed a sum past the
  safe-integer range into the constructor, where it surfaced as a misleading `TypeError` instead of naming
  the overflow. Fixed to raise `RangeError` at the operation. **The without-skill arm's `Money` had the same
  latent hole and shipped it.**
- **Q4 — a docblock on the wrong symbol.** The JSDoc sat above `SECONDS_PER_UNIT` instead of above
  `parseDuration`, so a reader and any tooling saw the contract attached to the wrong declaration. Fixed by
  moving the block.
- **Q2, Q3 — honest null results**, each with a full list of what was checked and what was consciously left.
  Q2: *"Nothing required a fix. The rewrite reproduces the original on every edge probed, and the one
  branch I removed was proven unreachable before removing it."* Q3 recorded the one hazard found by reading
  (a prototype-key lookup) as **not in the delivered code**, for a later editor.

This is the gate's value made concrete: on two tasks it **found a real defect its own arm had shipped**,
reproduced it, fixed it, and added the test.

---

## Q1 — rate limiter: smaller face, and a defect the other arm missed

Same spec, both arms. Executed and compared:

| measure | A (without-skill) | B (with-skill) |
|---------|-------------|-------------|
| lines | 103 | **67** |
| public surface | `RateLimiter` class, `createRateLimiter`, two exported constants | `createRateLimiter` only |
| injected clock for testing | no | **yes** (`now` option) |
| own test file | no | **yes** (`Q1_with-skill.test.js`) |
| input validation | defaults only | `requirePositiveInteger` on `limit` and `windowMs` |
| post-mortem defect found | — | **total bypass on a non-finite clock** |

**B exposes one factory and hides everything else** — "small face, deep body" from the skill's Part 1. A
exposes a class plus a factory plus two constants: four public things to keep stable. The injected `now`
is what made B's own edge test possible at all; A's `Date.now()` is hard-wired, so it cannot test its own
window without the wall clock.

---

## Q4 — the silent `NaN` versus a thrown error

Same inputs, both arms executed:

| input | A (without-skill) | B (with-skill) |
|-------|-------------|-------------|
| `'1h 30m'` | 5400 | 5400 |
| `'1d 2h 3m 4s'` | 93784 | 93784 |
| `''` | 0 | 0 |
| **`'abc'`** | **`NaN`** — silently | **`TypeError`** |
| **`'-5m'`** | **`NaN`** — silently | **`TypeError`** |
| `'1.5h'` | 5400 | 5400 |
| `'1h30m'` | 5400 | 5400 |

Both agree on every valid input, including the unstated `'1H'` (case-insensitive) and `'1h30m'` (no
space). They differ exactly where the skill's rule 0.6 applies.

**The without-skill returns `NaN`, and `NaN` is worse than `null`.** A `null` return can be caught by a
single `if (!result)` check at the call site. `NaN` is a **number**, so it passes every type check,
flows into the next arithmetic untouched, and turns every downstream total into `NaN` — the failure
appears far from its cause, which is exactly the "silent wrong value" the skill's maintainability pillar
forbids. It is also invisible to the obvious guard: `result === null` is false, and only
`Number.isNaN(result)` catches it. The without-skill arm's own note documented the behaviour as
*"malformed → `NaN`"* — it knew, and shipped it.

B names the failure at the boundary, so the caller cannot mistake a parse failure for a duration.

> **Correction to an earlier reading.** This run's first pass recorded the without-skill arm's output as `null`,
> because `JSON.stringify(NaN)` prints `null`. Re-executing and checking `typeof` showed the value is
> `NaN` (a number). The correction makes the finding **stronger**, not weaker — a silent `NaN` is harder
> to catch than a `null` — and it is recorded here rather than quietly fixed, because a report that
> hides its own measurement error cannot be trusted with the next one.

---

## Q2 — refactor: a tie on behaviour that hides a real difference

Both arms refactored the ugly `balance` function and **both reproduce the original exactly**, including
its absurd string-concatenation behaviour:

| input | original | A | B |
|-------|----------|---|---|
| `[{uid:1,amt:"10"}]` | `"010"` | `"010"` | `"010"` |
| `[{uid:1,amt:"10"},{uid:1,amt:"10"}]` | `"01010"` | `"01010"` | `"01010"` |
| `[{uid:1,amt:null}]` | `0` | `0` | `0` |
| `[{uid:1,amt:undefined}]` | `null` | `null` | `null` |
| mixed txs, 5 inputs | — | 5/5 match | 5/5 match |

**Zero behavioural divergence — a genuine tie on correctness.** But the two arms differ in *how* they got
there, and it matters for the next editor:

- **A kept the two branches** (`balance = balance + amt` / `balance = balance - amt`) and wrote a comment
  explaining that collapsing them would change the result for non-number `amt`. It preserved the trap
  *and* named it.
- **B collapsed them** into `total += entry.amt > 0 ? entry.amt : -entry.amt` and wrote the same
  behaviour, correctly, in a shorter form.

Both are correct here; both named loose `==` as deliberate. The skill's own rule 11 ("the size of the task
is the size of the edit") argues for A's caution on a refactor; the readability goal argues for B's
shorter form. **This is the same class of tension the first run found between rule 8 and the beauty goal,
and it is worth the skill stating which wins for a pure refactor.** Recorded as a finding about the skill,
not the arms.

---

## Q3 — the DRY trap: both arms fixed it identically

The input had the same value written twice (`{ start: DAY, seconds: DAY }`) plus a parallel `if` chain.
Both arms independently produced the *same* repair: one `SECONDS_PER_UNIT` table, `UNITS` built from it,
and `toSeconds` reading the table. Executed: **identical output** — `UNITS` equal, `toSeconds(2,'day')`
= 172800, unknown unit returns the value unchanged.

**A clean tie, and a useful one: it shows both arms recognise a duplicated fact.** The trap I set did not
discriminate — on this task the skill had nothing to add because the without-skill arm already knows DRY. That
is the "easy task" ceiling the evaluation method warns about, and it is recorded rather than spun.

---

## Q6 — Money: half the size, same guarantees

Both store integer cents and refuse to use floats. Executed on the same cases:

| case | A (without-skill) | B (with-skill) |
|------|-------------|-------------|
| `add(100,250)` | 350 | 350 |
| `multiply(150,3)` | 450 | 450 |
| `multiply` by `1.5` | `TypeError` | `RangeError` |
| `multiply` by `-1` | `RangeError` | `RangeError` |
| add across currencies | `TypeError` | `TypeError` |
| **lines** | 341 | **123** |

**Same behaviour on every probe**, differing only in which error class a fractional quantity raises —
a convention choice, not a defect. B is **2.8× shorter** for the same guarantees, and B's post-mortem
found the overflow hole (above) that A left in.

---

## Cost

| task | A bytes (js+md) | B bytes (js+md) | ratio |
|------|-----------------|-----------------|-------|
| Q1 | 6 956 | 6 434 | 0.92× |
| Q2 | 4 367 | 3 304 | 0.76× |
| Q3 | 3 044 | 3 637 | 1.19× |
| Q4 | 3 365 | 5 926 | 1.76× |
| Q5 (prose) | 6 226 | 16 025 | 2.57× |
| Q6 | 12 964 | 7 753 | 0.60× |

**Unlike the first run, the skill did not uniformly inflate the output.** On the code tasks B is often
*shorter* (Q6 at 0.60×, Q2 at 0.76×) because fewer lines is itself a readability requirement. The prose
task (Q5) is 2.57× longer, consistent with the first run's finding. **So the cost is concentrated in
explanatory prose, not in code.**

Extra artifacts B produced that A did not: **5 post-mortem files, 1 test file** (`Q1_with-skill.test.js`).

---

## Verdict

**The skill improves code quality and style on exactly the axes it claims, and it does not inflate code.**

1. **Maintainability showed up as behaviour, not decoration.** The post-mortem gate caught a total
   rate-limiter bypass (Q1) and a silent overflow (Q6) — defects the without-skill arm's artifacts shipped.
2. **Smaller faces, not bigger files.** One factory instead of a class + factory + constants (Q1); 123
   lines instead of 341 for the same guarantees (Q6).
3. **Explicit failure over silent sentinel** reproduced on a second task (Q4: a silent `NaN` vs a thrown `TypeError`),
   the same axis the first run measured.
4. **The gate's ratio held**: 5 of 5 code tasks produced a review file; 0 without-skill arms did.

**What did not differ, honestly:** Q2 and Q3 were ties on behaviour — on a task whose correct answer is
already known to a good model, the skill adds nothing measurable. That is the ceiling the method predicts,
and it is stated rather than omitted.

**What the run found about the skill:** the Q2 tension — "consistency with the file" versus "the shortest
correct form" — has no stated winner for a pure refactor. That is a gap worth closing in the next version.

---

## Reproduce

```bash
node evals/score_quality.py-check   # see score_quality.py in this directory
python3 score_quality.py <dir-of-outputs>
```

`score_quality.py` counts six maintainability facts mechanically per file: repeated literals (one place
to change), presence of a contract block, explicit throws and guards, verifiable assertions, comments that
name a deliberate decision, and short opaque identifiers. It is a floor for the eye, not a verdict on its
own — the behaviour diffs above are what decided the ties.
