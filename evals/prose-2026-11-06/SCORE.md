# Prose eval: the antibiotic-resistance article — 2026-11-06

Model: deepseek-v4.1-flash:1017 · one task, three arms · 11 checks, all decided without a judge.

## The task

An article of 1200–2500 words on why antimicrobial resistance cannot be postponed, with three demands
that a fluent text can fail: every figure carries who gave it and for which year; established fact,
estimate and forecast are separated by words, not by tone; and where estimates disagree, the range and
the reason for the disagreement are named.

## The checks

Ten template checks, each a thing prose can be wrong about in a verifiable way:

1. the attributable figure 1,27 million is present (GRAM, Lancet, 2019);
2. an associated figure in the 4,7–4,95 million band is present;
3. figures are marked as estimates;
4. the forecast is tied to 2050;
5. "10 млн" sits within 220 characters of 2050 — the classic error is quoting the forecast as today's toll;
6. at least three named sources or organisations;
7. uncertainty is named in words;
8. at least four section headings;
9. at least 1100 words;
10. no more than 3000 words.

An eleventh check was added after the first run, and it is the most interesting one:

11. **no CJK characters** — the plain arm wrote «Смешиватьこれらの вещи» in the middle of a Russian
    sentence. A language leak no reader-facing check would catch, and a template check catches in one line.

## Run one: equal budget, 12 000 tokens

| arm | words | failed checks |
|---|---|---|
| none | 1346 | 0 of 10 |
| graph | 496 | 2 — no article: stopped mid-graph |
| aggressive | 238 | 5 — no article: stopped mid-matrix |

Both planning arms were cut off inside their own plan. At this budget the graph is not a thinking aid,
it is a competitor for the same tokens as the text.

## Run two: 32 000 tokens

| arm | words | failed checks |
|---|---|---|
| none | 1258 | 0 of 11 |
| graph | 2463 | 0 of 11 |
| aggressive | 2376 | 0 of 11 |

All three pass every check at this budget. The planning arms write 1.9 and 1.9 times the length of the
plain arm, with the same score.

## What this actually says

**The first run's result was a budget artifact, not a finding.** I nearly reported "the graph makes the
model stop writing", which would have been false: it makes the model stop writing *at 12 000 tokens*,
where the plan alone eats the allowance. Same mistake as the 6000-token truncation in the code suite,
and the same fix — give every arm the budget the work needs, then compare.

**At equal and sufficient budget the checks do not separate the arms.** All three separate fact from
estimate, name sources, and tie the forecast to its year. This model already does the discipline the
prompt asked for; the graph did not add any.

**What the arms differ in is volume.** 1258 words against 2463. Whether that extra length is depth or
padding is not measured here, and saying "longer is better" without measuring it would be the exact
kind of comfortable claim this suite exists to prevent.

## What the suite cannot see

- whether the article is *true* beyond the ten anchors — no claim-level verification was run;
- whether the longer texts are better or merely longer;
- whether a reader would trust one more than another.

The next honest step for prose is claim extraction plus source verification: pull every sentence with a
number, check it against a small verified ledger, and count uncited specifics. That costs real search
per claim, which is why it is not in this run.

## Files

- `prompt.md` — the task as given;
- `article-none.md`, `article-graph.md`, `article-aggressive.md` — the three texts, unedited;
- `report.json` — every check, every answer.
