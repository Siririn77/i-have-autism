# Post-mortem: parseDuration

Module: `out/Q4_treated.js`. Green run before this look: `node Q4_treated.js` →
`parseDuration: all checks passed` (exit 0); `node --check Q4_treated.js` → no syntax errors.

## What I checked

- `null`, `undefined`, a number, and an array as `text` → `TypeError` before any string work; the
  `typeof` guard runs first, so no `text.trim is not a function` leak.
- Empty and whitespace-only string → `0`, deliberately not an error.
- `'5'` (bare number, no unit) → `TypeError`. Ambiguous between seconds and minutes, so it is rejected
  rather than guessed.
- `'-5m'` → `TypeError`; a leading sign is not in the grammar.
- `'1h 30'` (trailing number with no unit) → `TypeError`: the gap/trailing check sees `" 30"` as
  non-whitespace.
- `'1h 5x'`, `'1h,,30m'` (garbage between tokens) → `TypeError`.
- `'.5h'`, `'1..5h'` → `TypeError`; the number grammar requires a leading digit, so these are not read as
  decimals.
- Case: `'45S'`, `'1H 30M'` → correct; unit is lowercased before lookup.
- Whitespace forms: `'5 s'`, `'5s '`, newline and tab between tokens → all handled.
- Order and repeats: `'30m 1h'` → 5400; `'1h 1h'` → 7200 (repeated units sum).
- Huge magnitude: 400-digit day count → sum is `Infinity` → `TypeError`, not a silent `Infinity`.

## Found and fixed

- **Docblock was attached to the wrong declaration.** The JSDoc sat above `SECONDS_PER_UNIT` instead of
  above `parseDuration`, so a reader (and any tooling) saw the contract on the wrong symbol. Moved the block
  to `parseDuration`. No test needed; it is a placement fix.
- **Non-finite total could escape.** A number too large for a double summed to `Infinity` and was returned as
  a real answer. Added a `Number.isFinite` guard that throws `TypeError`, plus the 400-digit check above that
  exercises it.
- **Tests for the boundaries did not exist.** Added assertions for `'0s'`, `'1h 1h'`, `'1h 30'`, `undefined`,
  and the overflow case, so the contract for each is pinned.

## Left as is (deliberate)

- **Blank input returns `0` while a typo throws.** A missing duration means "no wait"; the two cases are kept
  distinguishable by throwing on anything that is not whitespace. Stated in the docblock and this file.
- **Precision beyond 2^53.** `'9007199254740993d'` returns an integer that is finite but not exact past 53
  bits. This is a property of IEEE-754 doubles, not of this function; seconds in any realistic duration stay
  well under that boundary, and the value is never `Infinity`. Documented, not guarded further.
