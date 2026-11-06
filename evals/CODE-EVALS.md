# Code evals: three arms, executed tests

The behaviour suite (`cases.json`) scores prose. This suite scores **code**: the answer's Python is
written to disk and run against a hidden unittest suite the model never sees. Only the interpreter
decides.

## The three arms

| arm | system prompt |
|---|---|
| `none` | a neutral coding assistant |
| `graph` | graph first — root questions, nodes with anchors, typed edges, stop rule |
| `ultra` | graph first + a cloud per node + a fidelity bar whose kind is a test |

Same user prompt in all three. Three samples per arm; the majority decides; partial score is the mean
fraction of tests passed.

## The tasks

| case | requirements | what it catches |
|---|---|---|
| `slugify` | 7 | non-ASCII words, separator runs, whole-word truncation at 60, single long word |
| `chunked` | 7 | empty input, string input, generator input, non-int and non-positive size |
| `csv_line` | 8 | quoted commas, escaped quotes, BOM, unclosed quote, text after a closing quote |
| `merge_intervals` | 7 | touching and nested intervals, unsorted input, invalid pair with numbers in the message |
| `rate_limiter` | 10 | lazy refill, capacity cap, atomic cost, injected clock, 200-thread race |

Four tasks are deliberately small. One is dense. The contrast is the point: **a graph is only worth its
tokens when the requirement list is dense enough that forgetting one is possible.**

## Calibration first

```
python3 evals/calibrate_code_evals.py
```

A reference implementation runs against every hidden suite before any model is asked. If a correct
implementation cannot pass, the test is the defect — not the model. This step caught two of its own
mistakes:

- `chunked` on a string: the spec said "works with a string", the test expected string slices — the spec
  now says the result is always a list of lists;
- `csv_line`: the reference accepted text after a closing quote — the parser now tracks `closed`.

Without this step both bugs would have been reported as model failures.

## Running

```
python3 evals/run_code_evals.py --repeat 3 --workers 3        # keep workers at 3
python3 evals/run_code_evals.py --id rate_limiter             # one case
```

The report lands in `evals/runs/code-report-<stamp>.json` with every answer and extracted code, so a
number can always be traced back to the text that produced it.

## Reading the report

```
case                 none         graph        ultra
rate_limiter         3/3          3/3          3/3
```

- `rate` — how many of three samples passed every test;
- `partial` — mean fraction of individual tests passed;
- `graphed` / `kpi` / `kpi_bars` — whether the arm actually produced the artefact it was told to
  produce, and how many bars it wrote. An arm told to graph and not graphing is not a graph arm,
  whatever the score says.

## Three ways this stand lied before it measured anything

Each of these read as a model failure and was mine:

1. a graph drawn in a ```text fence was extracted as code — the language became a condition;
2. once an answer carried both a solution and the tests that prove it, the last fence was the test
   suite — the extractor now skips blocks that import unittest or define `test_`;
3. a fence with no language held the plan in prose, and prose was imported as the solution — a
   candidate must now parse with `ast.parse`. No parseable block means no code, and the report says so.

A fourth, not a bug: an answer cut by the output budget produces a syntax error at the cut. The
report carries `truncated`, and a truncated sample is not evidence about the rule until the budget
covers the work the rule demands.
