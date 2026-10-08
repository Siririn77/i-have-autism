# T7_without-skill — rewrite note

Source: `/root/ab-test/t7_without-skill/proc.js`
Rewrite: `/root/ab-test/out/T7_without-skill.js`

## What changed

Readability only; no behavioural change.

- Meaningful names: `d`/`o`/`r`/`i`/`j`/`t` → `items`/`statusFilter`/`results`/`item`/`total`.
- Inverted the status test (`if (item.s == o || o == null)` → early
  `continue` when `statusFilter != null && item.s != statusFilter`) to cut
  nesting and make the skip case explicit.
- Extracted the per-item score into `scoreItem(item, alreadyScored)`:
  the amount check, the 10% discount and the duplicate-id check each read
  as one statement instead of a nested block and a scan loop that mutated
  `t` to `0`.
- Replaced the "set `t = 0` if a prior row has the same id" trick with an
  explicit `isDuplicate ? 0 : total` return.
- Replaced the inner duplicate scan with `Array.prototype.some`, which
  keeps the same loose `==` comparison.
- Added JSDoc and short comments documenting the rules and the sort.
- Kept `module.exports = { proc }` and both parameters' arity.

## Behaviour preserved deliberately

- **Loose equality is kept.** `==`/`!=` are used for both the status and id
  comparisons so numeric and string ids/statuses keep matching each other.
  `!=`/`==` against `null` also still matches `undefined`, so a `null`
  *and* an `undefined` filter behave identically, as before.
- **Filter check order unchanged:** the status filter is still tested
  before the amount, so an item excluded by status never contributes.
- **Duplicate handling unchanged:** only the first occurrence of an id is
  kept — later rows with the same id score 0 and are not pushed.
- **Sort unchanged:** descending by `total`, using the same comparator, so
  V8's stable sort keeps ties in insertion order.
- Only rows with `total > 0` are pushed; the item object is never mutated.

## Verification

Ran a differential test (`/root/.hermes/profiles/ougi/cache/scratch/t7_diff.js`)
comparing `proc` from both files over 5000 randomized inputs (mixed
numeric/string/null ids and statuses, amounts of 0 / negative / fractional,
falsy `c` variants) plus 9 hand-picked edge cases (empty input, zero/negative
amount, duplicate ids, mixed-type duplicate ids, null filter). `JSON.stringify`
of both results was identical in all **5009** cases — 0 mismatches.
