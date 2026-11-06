# Code evals — 2026-11-06

Model: deepseek-v4.1-flash:1017 · 3 samples per arm · tests executed, not matched.

## Result

| case | none | graph | aggressive |
|---|---|---|---|
| slugify | 3/3 | 3/3 | 3/3 |
| chunked | 3/3 | 3/3 | 3/3 |
| csv_line | 3/3 | 3/3 | 3/3 |
| merge_intervals | 3/3 | 3/3 | 2/3 |
| rate_limiter | 3/3 | 3/3 | 3/3 |
| **cases passed, все 3 пробы** | **5/5** | **5/5** | **4/5** |
| cases passed, большая часть проб | 5/5 | 5/5 | 5/5 |
| mean fraction of tests | 1.00 | 1.00 | 0.93 |
| graph produced | 0/5 | 4/5 | 0/5 |
| matrix produced | 0/5 | 0/5 | 0/5 |
| register produced | 0/5 | 0/5 | 0/5 |

Две строки намеренно различаются: строгая считает случай пройденным только если все три пробы зелёные,
мягкая — если большинство. Для `merge_intervals × aggressive` это 2 из 3, то есть мягко пройдено, строго нет.
Раннер печатает мягкую; в таблице выше ведущая строка — строгая.

## What it says

1. **On these tasks the graph changes nothing.** Five tasks, all requirements written out explicitly, and
   the model solves every one in every arm. There is no headroom for a graph to recover: nothing was
   forgotten, so nothing was there to be found.
2. **The aggressive instructions were dropped entirely.** Zero matrices, zero registers, zero graphs, in
   all fifteen aggressive samples. The system prompt asked for a coverage matrix; the model answered the
   question. A long instruction set loses to a short concrete request.
3. **Aggressive cost one case.** `merge_intervals` failed one of three aggressive samples — the only
   failure in the whole run — while the same task passed 3/3 in the other two arms. With n=3 this is a
   data point, not a trend, but it is not evidence in favour of the mode either.

## Two harness defects caught before the model was judged

Both would have been reported as model behaviour:

- **`chunked` spec vs test.** The spec said "works with a string"; the test expected string slices. The
  spec now says the result is always a list of lists. A correct implementation had failed.
- **`csv_line` reference.** The reference parser accepted text after a closing quote, which rule 8
  forbids. Fixed by tracking `closed`.

Then, in the first two runs of the eval itself:

- **A graph drawn in ```text was extracted as the code** — the extractor took the last fence regardless
  of language, so a correct answer scored 0 with the graph's prose as "solution.py". The extractor now
  reads the language tag and takes the last python block.
- **The token budget cut the code after the graph.** At 6000 tokens a graphed answer ended mid-line; the
  arm looked worse for a reason that had nothing to do with graphs. The budget is now 9000 for code
  cases.

Every one of these four produced a "difference between arms" that was the harness, not the model. That is
the usual way an A/B test lies.

## Conclusion

Graphization pays where the requirement surface is wide enough that omission is possible: a series, a
course, a book, a plan with fifty parts. A single-file function with seven rules is not that surface. For
code the honest recommendation is the one already in the skill: three to five nodes as comments when the
task is non-trivial, nothing when it is a one-liner — and never aggressive mode.

## What this suite cannot yet tell us

The tasks are too easy for this model. To measure the effect honestly the suite needs tasks where a
written requirement list is long enough that a competent implementation still misses one: a config
merger with fourteen interacting rules, a scheduler with injected clock and priority inversion, a
migration with rollback and partial failure. Until then the numbers above say "no difference", not "graph
is useless".
