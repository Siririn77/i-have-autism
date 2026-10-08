# Rewrite note: proc.js

Rewritten to `/root/ab-test/out/T7_treated.js`. Observable behaviour is unchanged.

## What changed (readability only)
- **Names.** `d`/`o`/`r`/`t`/`a`/`p`/`s`/`c` became `orders`/`sellerId`/`accepted`/`total`/… and each loop item is bound once as `order`.
- **Early `continue` instead of nested `if`.** The seller filter and the amount check are now guards, so the main path runs top to bottom with no indentation staircase.
- **Duplicate check named.** `r[j].id == d[i].id → t = 0` became `accepted.some((entry) => entry.id == order.id)` with an early `continue`, so "this id is already listed" is stated once instead of encoded as "set total to zero so it fails the next test".
- **Sort extracted to one expression** and `var` → `const`/`let` in block scope.

## Behaviour kept exactly
- Loose equality (`==`, not `===`) is preserved for both `s` and `id`. `1` and `'1'` still match each other.
- `o == null` still tests `null` **and** `undefined`; rewritten as `sellerId != null` inverted, same set.
- The `a > 0` gate uses the same coercion (e.g. `'3' > 0` is true, `NaN > 0` is false), written as `!(order.a > 0)`.
- `!order.c` truthiness (discount when `c` is absent/`false`/`0`/`null`/`''`) is unchanged; the multiplier `*= 0.9` gives the same float result.
- `total > 0` still drops non-positive totals *after* the discount.
- Output objects are exactly `{ id, total }`, sorted by `total` descending; the array is returned, not the input, and the input array is not mutated.

## Verification
`/root/ab-test/out/_diff_test.js` diffs old vs new:
- 200,000 randomized orders (mixed numeric/string ids, `NaN`, negatives, `0`, missing `c`) → **0 mismatches** in `JSON.stringify` output.
- 13 fixed edge cases (empty array, `undefined` sellerId, `'1'` vs `1`, zero amount, `NaN` amount, duplicate ids across types) → all match.
- Array-like non-iterable input → both produce the same result (no `for…of` introduced).
