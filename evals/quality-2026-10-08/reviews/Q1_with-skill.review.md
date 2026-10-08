# Post-mortem: out/Q1_with-skill.js

Green run before this review: `node --test Q1_with-skill.test.js` → 7/7 pass, 0 fail; `node --check` on both
files → clean; ESLint (`eslint/bin/eslint.js`, default config, no lookup) → exit 0, no errors.

## What I checked
- `userId` of the wrong type (`null`, `undefined`, `''`, `42`, `{}`, `[]`) → `TypeError` naming the value;
  never a silent `false`. The one wrong meaning `false` could carry — "you are rate-limited" — is kept
  distinct from "you called me wrong".
- `limit` = `0`, `2.5`, `undefined`, negative; `windowMs` negative; `now` not a function → all `TypeError`
  at construction, before any state exists. A bad configuration cannot become a silently-always-rejecting
  limiter.
- Exact window edge: a request with age equal to `windowMs` is expired (half-open `(start, now]`). Pinned by
  a test, because `<` versus `<=` is exactly where an off-by-one hides.
- Rejected calls: do not consume allowance and do not extend the window. Verified that a rejected call still
  writes the pruned array back, so repeated rejections do not strand stale timestamps.
- Independence across users (distinct Map keys) and a defaulted `windowMs` (60000) when omitted.
- Storage bound: a user can hold at most `limit` timestamps at once, so per-user memory is bounded even
  though nothing is evicted.

## Found and fixed
- A clock returning a non-finite value (`NaN`, `Infinity`, a string, `null` via a mis-wired `now`) made
  `check` always return `true`: `time > windowStart` compares false against `NaN`, so no timestamp ever
  counted and the limiter silently vanished — a total rate-limit bypass with no error. Fixed by guarding
  `now()`'s return with `Number.isFinite` and throwing, plus a test over `[NaN, Infinity, '0', null]`. This is
  the loud-failure rule applied where it actually mattered, not decoration.

## Left as is (deliberate)
- Memory for a user who never returns is not reclaimed. The module is explicitly in-memory and small; an
  eviction mechanism (sweep timer / LRU cap / delete-on-empty) is a third caller's problem, not this one's.
  Named here so the next editor sees it is a decision, not an oversight.
- `check` is not thread-safe across real OS threads — JavaScript on this runtime is single-threaded per
  isolate, and the state is a plain `Map`, so concurrent calls within one process are serialized by the
  event loop. Across worker threads the limiter would need to be shared through `SharedArrayBuffer` or a
  per-thread instance; out of scope for an in-memory limiter.
- `describe(NaN)` renders `"null"` because `JSON.stringify(NaN)` is `"null"`. Only affects the wording of an
  error message; the value still triggers a throw. Cosmetic, left alone.
