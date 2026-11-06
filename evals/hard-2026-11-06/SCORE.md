# Hard case: mini-DB — 2026-11-06

Model: deepseek-v4.1-flash:1017 · one task · three arms · 26 hidden tests, executed.

## The task

A single-file mini-DB: transactions over an in-memory store, snapshot isolation, write-write conflict
detection, an append-only journal with checksums, durability across reopen, a torn last record ignored,
ids never reused, unicode data. Fourteen numbered requirements. The reference solution is 190 lines; the
model's answers are 380.

This is the first task in the suite where the requirement surface is wide enough that a competent
implementation can still miss a piece — the thing the easy code suite could not test.

## Result

| arm | tests | lines | notes |
|---|---|---|---|
| `none` | **26/26** | 380 | `Database`, `Transaction`, `ConflictError`; sha256 per record, fsync on commit |
| `graph` | **26/26** | 377 | same architecture, plus a task graph in the answer and six extra helpers (`_truncate_to`, `_check_conflicts`, `_view_tables`) |
| `aggressive` | **26/26**, 2 of 2 on retry | 17k chars | see below |

## The one event worth reporting

The first aggressive run returned **an empty answer at 64 000 tokens** (`finish_reason=length`): the
model spent the whole budget inside reasoning and emitted nothing — no graph, no code. Two repeats
afterwards passed cleanly.

So the aggressive prompt is not reliably unusable on hard tasks; it is reliably **expensive**, and one
run in three blew the ceiling without producing a character.

## What the aggressive arm actually produced — corrected after reading the answers

Not nothing. Both successful aggressive runs open with a task graph, and both carry a register of
decisions; one of the two also carries a coverage matrix. So the instruction set was followed, and the
artefacts exist. They are simply large: 17 013 and 16 539 characters against 10 655 for the plain arm —
roughly 60 % more output for the same 26/26.

Cost, measured: the three sequential runs took 16 m 23 s wall clock, about 5.5 minutes each.

## What it actually built

Both working solutions converge on the same design, which is the right one:

- committed state in memory, snapshot copied at `begin()`;
- a per-row version counter set to the commit sequence, so a write-write conflict is one comparison;
- the journal as one JSON record per commit with a checksum, `fsync` before the in-memory apply;
- replay stops at the first line without a trailing newline, so a torn tail is dropped instead of
  guessed at.

The difference the graph made is visible in the helper list, not in the score: the graph arm factored the
replay into `_apply_op` / `_truncate_to` and the isolation into `_view_tables` / `_check_conflicts`. More
named pieces, same behaviour.

## Two defects in the reference, caught before the model was judged

The suite is only worth its result if a correct implementation passes it. Mine did not, at first:

- `select` unpacked `sorted(view.items())` as three values instead of two — eleven errors;
- the checksum was computed over the record body including its trailing newline on write and excluding it
  on read — so every journal failed to replay and three durability tests failed.

Both fixed; the reference now passes 26/26. Had I skipped calibration, the report would have said "the
model cannot do durability", which would have been false.

## Files

- `prompt.md` — the specification as given;
- `solution-none.py`, `solution-graph.py` — the two answers, unedited;
- `report.json` — every answer, every test outcome.

## Conclusion

At this difficulty the model does not fail; it converges on a correct design in all three arms. The
differentiator is not correctness but cost: the graph arm adds a plan and no score, the aggressive arm
adds a plan plus a register (plus a matrix in one run of two) and no score, and one aggressive run out of
three spent 64 000 tokens to produce nothing at all.

To separate the arms honestly the task has to be larger than one file: several modules, an interface
between them, and a requirement that cannot be satisfied locally. That is the next rung, and it needs a
test harness that runs a whole package rather than one `solution.py`.
