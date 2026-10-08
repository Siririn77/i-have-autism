# Post-mortem: out/Q2_with-skill.js

## Green run first

`node --check out/Q2_with-skill.js` — clean. Differential harness (`scratch/diff_test.js`,
24 cases comparing the original and the rewrite with `Object.is`): `cases=24 failures=0`.

## What I checked

- **Match / no-match / empty / `null` / `undefined` / primitive collections** → identical to the
  original; `for...in` over `null`, `undefined`, and a number yields no keys in both, so both return 0.
- **Loose id equality** (`1` vs `"1"`, both directions) → both match; the rewrite keeps `!=`, so the
  behaviour is preserved deliberately.
- **Magnitude sign** (negative, zero, `-0`, mixed) → both sum the magnitude; totals are non-negative.
- **`NaN`, `undefined`, `null`, missing `amt`** → both propagate the same value (`NaN` total, or the
  same coerced result); the rewrite's ternary is a literal copy of the original branches.
- **String `amt`** (`'5'`, `'-5'`, `'05'`) → both produce the identical value including the original's
  string-concatenation quirk (`0 + '5'` becomes `'05'`), confirmed by the harness.
- **Overflow** (`1e308 + 1e308`) → both yield `Infinity`.
- **Inherited enumerable property via prototype** → both visit and sum it; `for...in` was kept.
- **Removed clamp `if (r < 0) r = 0;`** → the running total can never be negative (each matched entry
  contributes a non-negative magnitude) and `x < 0` is false for `NaN` and numeric strings, so the
  branch was unreachable; removing it cannot change any return value. Verified across the corpus.

## Found and fixed

- Nothing required a fix. The rewrite reproduces the original on every edge probed, and the one branch
  I removed was proven unreachable before removing it.

## Left as is (deliberate)

- **`for...in` retained** — swapping it for `for...of`/`.forEach` would drop inherited and non-index
  enumerable properties, a behaviour change.
- **Loose `==` retained** — tightening it to `===` would stop matching `1` to `"1"`.
- **Non-numeric `amt` coercion retained** — including the string-concatenation quirk, which is
  observable output.
- **Silent `0` for a non-collection `entries`** — the original does not throw; throwing would be a
  behaviour change, so the contract in the JSDoc documents the real behaviour instead.
