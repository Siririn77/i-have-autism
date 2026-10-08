# Post-mortem: out/Q6_treated.js (Money)

Green run before this read: `node --check out/Q6_treated.js` clean; assertion
run over the module (`assert` from Node stdlib) — ALL ASSERTIONS PASSED.

## What I checked

- **Non-integer `minorUnits` (`1.5`)** → `TypeError` at the constructor. A float
  amount is exactly the defect the module exists to prevent; it is refused, not
  rounded.
- **String amount (`'100'`)** → `TypeError`. No implicit `Number()` coercion
  sneaks a `'100'` (or a `'10abc'` → `NaN`) through.
- **`NaN` / `Infinity` amount** → `TypeError` (`Number.isSafeInteger` is false
  for both).
- **Currency mismatch (`USD.add(EUR)`)** → `TypeError` naming both codes. No
  silent rate.
- **Foreign operand (`usd.add({minorUnits, currency})`)** → `TypeError`; a duck
  object with the right shape is refused, so a bug cannot pass as a `Money`.
- **Fractional quantity (`multiply(1.5)`)** → `RangeError`. Deliberate; see the
  code comment.
- **Negative quantity (`multiply(-1)`)** → `RangeError`.
- **Zero amount (`new Money(0,'USD').multiply(1000)`)** → `0`. Correct: zero
  times anything is zero, no special case needed.
- **Operand mutation** → `add` and `multiply` return a new frozen object; both
  operands keep their `minorUnits`. `Object.freeze(this)` in the constructor
  means an external `m.minorUnits = 5` is a no-op in strict mode (throws in
  sloppy mode) rather than a silent corruption.
- **`currency` empty / non-string** → `TypeError`.
- **Huge values** → see "Found and fixed".

## Found and fixed

- **Silent rounding on overflow.** Before the fix, `add` computed
  `this.minorUnits + other.minorUnits` and passed it to the constructor; a sum
  past `Number.MAX_SAFE_INTEGER` is no longer an exact integer, so the
  constructor threw `TypeError` saying the *result* "must be a safe integer" —
  which points the reader at the constructor, not at the real cause (the
  operands overflow the range when combined). `multiply` had the same shape.
  Fix: `requireExactSum` and `requireExactSpan` guard both, and throw
  `RangeError('... overflows the safe integer range')` at the operation. Test
  added: `MAX_SAFE_INTEGER + 1` and `MAX_SAFE_INTEGER * 2` now throw
  `RangeError`, message names the overflow.
- (There was no test file in the repo for this module; the assertions in the
  verification note are the covering tests, run inline. A sibling `.test.js`
  was not added because nothing in the project defines a test runner — adding
  one would be a mechanism before its second caller.)

## Left as is (deliberate)

- **Currency case-sensitivity (`'usd'` vs `'USD'`).** Left exact-match. Two
  spellings of one currency are a normalisation concern, and normalising here
  would silently accept `'usd'` and then reject `'USD'`-formatted input
  elsewhere; the caller owns the canonical spelling.
- **No `toString` / formatting.** Out of scope for this task (handling amounts),
  and formatting is locale-dependent — a second caller for it does not exist
  yet.
- **No `subtract`.** `add(new Money(-x, cur))` already expresses subtraction,
  and negative amounts are supported. A `subtract` method would be a second
  spelling of `add`, not a second fact.
- **`minorUnits` and `currency` are plain fields, not getters.** They are
  read-only by `Object.freeze`; a getter pair would add surface without adding
  a guarantee.
- **`multiply` refuses fractional quantities rather than rounding.** This is a
  decision, not an omission: the rounding rule belongs to the business rule that
  needs it. Documented in the docblock so the next editor does not "fix" it by
  adding `Math.round`.
