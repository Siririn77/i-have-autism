# T3 — parseConfig bug fix

## The bug

`parseConfig` did:

```js
const [key, value] = line.split('=');
out[key.trim()] = value.trim();
```

`String.split('=')` returns an array of length 1 for any line that contains no `=`
(e.g. an empty string, blank lines, comment/header lines). In that case `value` is
`undefined`, and `value.trim()` throws `TypeError: Cannot read properties of undefined
(reading 'trim')`. `parseConfig('')` crashes immediately because `''.split('\n')`
yields `['']`, and `''.split('=')` yields `['']`.

Two further latent issues: a line like `url=a=b` would lose everything after the
second `=` (destructuring only captures the first two elements), and whitespace-only
lines could produce an empty-string key.

## The fix

- Trim each line first; skip empty lines and `#` comments.
- Find the **first** `=` with `indexOf`; if absent, skip the line instead of crashing.
- Split on that first `=` only, so values may themselves contain `=` (`url=a=b=c` kept intact).
- Skip lines with an empty key.
- Coerce input via `String(text)` to avoid crashing on `null`/`undefined`.

## Verification

Ran the fixed module against: empty string, blank lines, comment lines, lines with no
`=`, values containing `=`, and lines with surrounding whitespace. All return correct
objects with no exceptions. Output:

```
empty string => {}
blank lines => {"a":"1","b":"2"}
comment => {"a":"1"}
line no equals => {"a":"1","b":"2"}
value with equals => {"url":"a=b=c"}
spaces => {"key":"value"}
```
