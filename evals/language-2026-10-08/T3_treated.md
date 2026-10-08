# Bug and fix: parseConfig

Fixed file: `/root/ab-test/sandbox7_treated/src/parse.js`

## The bug

`parseConfig` crashed with `TypeError: Cannot read properties of undefined (reading 'trim')` on any line that has no `=` character.

Cause: `line.split('=')` returns an array of length 1 when the separator is absent. Destructuring `const [key, value] = ...` then leaves `value` as `undefined`, and the next line calls `value.trim()`, which throws.

The crash triggers more often than it looks: `''.split('\n')` returns `['']` (one empty line), so empty input crashes. A trailing newline (`'a=1\n'`) leaves a final empty line and crashes. A blank line between entries crashes. Any line without `=` crashes.

## The fix

Instead of `split('=')` and destructuring, find the first `=` with `indexOf` and slice around it:

- `indexOf` returns `-1` when there is no `=` → the line is skipped with `continue`.
- `slice(0, i)` is the key, `slice(i + 1)` is the value; both are always strings, so `trim()` is safe.

Skipping malformed lines also fixes a second, silent defect: the old code split on **every** `=` and kept only the first two pieces, so `a=b=c` produced `a` → `b` and dropped `=c`. The fix keeps the whole value after the first `=`, so `a=b=c` → `a` → `b=c`.

## Verified inputs (no crash)

| Input | Result |
|---|---|
| `''` | `{}` |
| `'\n'` | `{}` |
| `'a=1\n\nb=2'` | `{ a: '1', b: '2' }` |
| `'novalue'` | `{}` |
| `'a=1\n'` | `{ a: '1' }` |
| `'a=b=c'` | `{ a: 'b=c' }` |
| `'  spaced  =  v  '` | `{ spaced: 'v' }` |
| `'x=1\r\ny=2'` | `{ x: '1', y: '2' }` (CR trimmed) |
| `'empty='` | `{ empty: '' }` |

## Left as is (deliberate)

- A line with an empty key (`'=nokey'`) yields `{ '': 'nokey' }`. This does not crash. Handling it is a separate question of validation policy, not part of this bug.
- No comment lines (`#`) or other config syntax was added; the function still only understands `key=value`.
