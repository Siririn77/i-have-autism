# Post-mortem: out/Q3_with-skill.js

## Green run first

Before this read: `node --check out/Q3_with-skill.js` — clean. ESLint
(`no-undef`, `no-unused-vars`, `no-fallthrough`, ecmaVersion 2022) — exit 0 on both the
original and the rewrite. Differential harness (`scratch/q3_diff.js`, 330 cases comparing
the original and the rewrite with `Object.is`): `cases=330 failures=0`; `UNITS` JSON,
exported key set, and `toSeconds.length` all identical. Then the code was read as a
stranger's.

## What I checked

- **`UNITS` construction** → `Object.values` yields `[86400,3600,60]` in insertion order,
  and `.map` builds `{start, seconds}` with `start` first, so the array and its key order
  match the original exactly. Confirmed by string equality of the JSON.
- **Unknown / empty / differently-cased unit** (`'second'`, `''`, `'DAY'`, `'Day'`) →
  both return `value`. The original matched by `===`; the rewrite's `Object.hasOwn`
  returns false for all of them.
- **Prototype keys** (`'toString'`, `'valueOf'`, `'hasOwnProperty'`, `'constructor'`,
  `'__proto__'`) → both return `value`. This is the trap the rewrite had to avoid: a
  lookup written as `SECONDS_PER_UNIT[unit] !== undefined` or `unit in SECONDS_PER_UNIT`
  would match `'toString'` and return `value * [function]` = `NaN`, a behaviour change.
  `Object.hasOwn` rejects inherited keys, matching the original. Verified in the harness.
- **Non-string unit** (`0`, `1`, `false`, `true`, `null`, `undefined`, `NaN`, `{}`, `[]`)
  → both return `value`; the table has no numeric keys, so `Object.hasOwn` is false.
- **Non-number `value`** (`'3'`, `'-2'`, `undefined`, `null`, `{}`, `[]`) → both compute
  the same coerced product (`'3' * 86400` = `259200`), because the rewrite multiplies by
  the same table value the original multiplied by.
- **Numeric edges** (`0`, `1`, `-1`, `-0`, `0.5`, `NaN`, `Infinity`, `1e308`) → identical,
  including `1e308 * 600` → `Infinity`.
- **Exported surface** → `module.exports` keys and `toSeconds.length` unchanged, so
  existing callers that destructure or inspect arity see no difference.

## Found and fixed

- No shipped defect required a fix; the harness reported zero mismatches on the first
  run. The one design hazard found during the read was the prototype-key lookup described
  above — it is not in the delivered code, and it is recorded here so a later editor who
  rewrites the lookup does not reintroduce it (a test case for `'toString'` covers it).

## Left as is (deliberate)

- **`start` kept on every `UNITS` row.** It duplicates `seconds` by definition, but it is
  part of the module's exported data and dropping it would be an observable change. The
  duplication is neutralised at construction: both fields are built from one value, so
  they cannot diverge.
- **`Object.hasOwn` retained over `Object.prototype.hasOwnProperty.call`.** `Object.hasOwn`
  is cleaner and requires Node 16.9+. The project runs Node 26, stated in the environment,
  so the portability cost is zero here; the call form was the alternative if a lower floor
  were needed.
- **`UNITS` is not frozen.** A caller can still mutate the exported array, desyncing it
  from the table. The original array was mutable too and freezing it is a behaviour
  change, so it is left mutable.
- **No input validation added** (`throw` on an unknown unit). The original returns `value`
  for an unknown unit; throwing would be a behaviour change. The contract is documented in
  the docblock instead, so the next editor sees the real behaviour without having to run
  it.
