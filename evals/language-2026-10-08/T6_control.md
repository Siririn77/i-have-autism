# `applyDelta.js` — line-by-line walkthrough

File: `/root/ab-test/t6_control/applyDelta.js` (12 lines)

## What it does, in one sentence
It merges a bag of numeric deltas into a running counter object on a `state`
record, but only if the same record has not been touched within the last
60 seconds; the throttled calls are silently dropped and the unchanged `state`
is returned.

## Line by line

```js
function applyDelta(state, delta) {
```
Declares the module's only public function. It takes two arguments:
- `state` — the mutable record being updated. It is expected to already carry a
  `counters` object; the function also reads/writes a `lastSeen` field on it.
- `delta` — a plain object mapping counter names to numbers to add
  (e.g. `{ hits: 3, errors: 1 }`).

```js
  const now = Date.now();
```
Captures a single timestamp (milliseconds since the Unix epoch) once, up front.
Taking it once means the throttle comparison below uses one consistent clock
reading rather than re-reading the time mid-function.

```js
  if (state.lastSeen && now - state.lastSeen < 60000) {
    return state;
  }
```
The throttle / rate-limit guard. `60000` ms = 60 seconds (written as a magic
number rather than a named constant).
- If `state.lastSeen` is falsy (never set, or `0`/`undefined`), the `&&` is
  false and the guard is skipped — so a fresh record always passes.
- Otherwise it checks whether *less than* one minute has elapsed since the last
  applied delta. If so, the function returns the original `state` **untouched**
  — the incoming `delta` is discarded, no counters change. Note it returns
  `state`, not `null`/`undefined`, so callers cannot distinguish "dropped" from
  "applied" except by inspecting the counters.

```js
  state.lastSeen = now;
```
Records that a delta was accepted at this moment. This is what starts the next
60-second window. It is set *before* the merge, so even a merge that encounters
a bad input value has already claimed the window.

```js
  for (const [k, v] of Object.entries(delta)) {
```
Iterates every own enumerable key of `delta` as `[key, value]` pairs.
`Object.entries` ignores inherited/prototype properties, so only the caller's
own fields are processed.

```js
    state.counters[k] = (state.counters[k] || 0) + v;
```
The actual accumulation. For each key it reads the existing counter (treating a
missing/zero entry as `0` via `||`), adds the delta value `v`, and writes it
back. This **creates** counters on first sight, so `state.counters` need not be
pre-populated with every key. Two caveats worth knowing: `||` also resets any
counter whose current value is `0`-ish (harmless here since adding `0` yields
the same result), and nothing validates that `v` is a number — a non-numeric
`v` would produce `NaN`.

```js
  }
```
End of the loop.

```js
  return state;
```
Returns the same object reference that was passed in. The function mutates in
place rather than returning a copy, so the caller's object is updated
regardless of whether they look at the return value. Both branches return
`state`, giving a consistent shape to callers.

```js
module.exports = { applyDelta };
```
CommonJS export. Consumers use `const { applyDelta } = require('./applyDelta')`.

## Behaviour summary / things to watch
- **Side-effecting and throttled:** mutates `state` in place; at most one merge
  per 60-second window per `state` object.
- **Dropped deltas are lost**, not queued or retried.
- **Return value cannot signal a drop** — callers must compare counters or
  `lastSeen` to tell what happened.
- Assumes `state.counters` already exists; a `state` without it will throw
  (`Cannot set properties of undefined`) once a delta is applied.
- `60000` is an inline magic constant; extracting a named
  `THROTTLE_MS` would make the intent clearer.
```
