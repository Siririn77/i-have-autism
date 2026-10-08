# `applyDelta.js` — line by line

File: `t6_with-skill/applyDelta.js` (12 lines, 321 bytes).

## Source

```js
 1  function applyDelta(state, delta) {
 2    const now = Date.now();
 3    if (state.lastSeen && now - state.lastSeen < 60000) {
 4      return state;
 5    }
 6    state.lastSeen = now;
 7    for (const [k, v] of Object.entries(delta)) {
 8      state.counters[k] = (state.counters[k] || 0) + v;
 9    }
10    return state;
11  }
12  module.exports = { applyDelta };
```

## What it does, in one sentence

`applyDelta` adds the numbers inside a `delta` object to the matching keys of a `state.counters`
object, but only at most once every 60 seconds; if called again sooner, it returns the state unchanged
and drops the incoming delta.

## Line by line

**Line 1 — `function applyDelta(state, delta) {`**
Declares the function and its two inputs:
- `state` — a mutable object that holds `state.counters` (an object of name → running total) and
  `state.lastSeen` (a timestamp in milliseconds, written by this function).
- `delta` — an object whose keys are counter names and whose values are the amounts to add.
The function mutates `state` in place; it does not copy it.

**Line 2 — `const now = Date.now();`**
Reads the current time once, as milliseconds since 1970 (Unix epoch), and stores it in `now`.
It is read once so that the guard on line 3 and the write on line 6 use the same moment.

**Line 3 — `if (state.lastSeen && now - state.lastSeen < 60000) {`**
The rate-limit guard. It is true only when both parts hold:
1. `state.lastSeen` is truthy — i.e. this function has run before and set it.
2. `now - state.lastSeen < 60000` — fewer than 60,000 ms (60 seconds) have passed since that run.

The `state.lastSeen &&` prefix is a "have we ever run?" test. Because `0` and `undefined` are falsy,
a state whose `lastSeen` is `0` or missing is treated as never-seen and passes the guard. This is
intended: a brand-new state should apply its first delta immediately.

**Line 4 — `return state;`**
When the guard is true (called within 60 seconds of the previous run), the function returns the state
**without applying `delta`**. The delta is not stored, buffered, or replayed later — it is discarded.

**Line 6 — `state.lastSeen = now;`**
Records this run's timestamp. This is what arms the 60-second guard for the next call. It happens
before the counters are updated.

**Line 7 — `for (const [k, v] of Object.entries(delta)) {`**
Loops over the delta's own key/value pairs. `Object.entries(delta)` returns an array of `[key, value]`
pairs; the loop destructures each into `k` (counter name) and `v` (amount to add). Order follows
normal own-property order (string keys in insertion order, integer-like keys first).

**Line 8 — `state.counters[k] = (state.counters[k] || 0) + v;`**
Adds `v` to the existing counter for `k`:
- `state.counters[k]` reads the current total; if it is `undefined`, `0`, `""`, `null`, or `NaN`,
  the `|| 0` substitutes `0`, so a first-time key starts from zero.
- `+ v` adds the delta amount.
- The result is written back into `state.counters[k]`.

Important detail: `+` is not guaranteed to be numeric addition. If a value is non-numeric — e.g. the
string `"9"` — the `+` performs string concatenation, so `(undefined || 0) + "9"` yields the string
`"09"`, not the number `9`. Counters are only reliable when every `v` is a number.

**Line 10 — `return state;`**
Returns the same `state` object that was passed in (the same reference, mutated). Line 4 and line 10
both return `state`, so the return value is always the live state object, never a new one.

**Line 12 — `module.exports = { applyDelta };`**
Exports the function as a named property for `require`-based (CommonJS) consumers:
`const { applyDelta } = require("./applyDelta.js");`

## Behavior you can rely on (verified by running it)

- First call with a fresh state applies the delta and sets `lastSeen`:
  `applyDelta({ counters: {} }, { x: 5 })` → `{ counters: { x: 5 }, lastSeen: <now> }`.
- A second call within 60 seconds does nothing: it returns `{ counters: { x: 5 } }` unchanged, and the
  new delta `{ x: 5 }` is lost.
- The returned value is the **same object** passed in (`result === state` is `true`). The function has
  a side effect — it mutates its argument — despite the neutral-looking name.

## Assumptions this code makes, and where it breaks

These are the inputs the code does not mention. State them so nobody is surprised.

1. **`state.counters` must exist.** Line 8 reads `state.counters[k]`. If `state` has no `counters`
   property, it throws `TypeError: Cannot read properties of undefined (reading '<key>')`.
   The caller must pass `{ counters: {} }` at minimum.
2. **Deltas inside the 60-second window are dropped, not deferred.** A caller that sends `{ x: 5 }`
   twice in a minute ends up with `x === 5`, not `10`. If deltas are expected to accumulate, this is a
   data-loss bug; if the design is "one event per minute", it is correct by intent.
3. **`v` must be a number.** A numeric string concatenates (`0 + "9"` → `"09"`). Guard at the call site
   or validate inside the loop if `delta` can arrive from JSON or a request body.
4. **`now` comes from `Date.now()`**, which is wall-clock time. A backwards clock adjustment can make
   `now - lastSeen` negative — still `< 60000`, so the guard treats it as "too soon" and skips.

## Minimal correct usage

```js
const { applyDelta } = require("./applyDelta.js");

const state = { counters: {} };
applyDelta(state, { requests: 1 });   // applies
applyDelta(state, { requests: 1 });   // ignored — within 60 s
// 60 s later
applyDelta(state, { requests: 1 });   // applies
```
