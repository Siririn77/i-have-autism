# Review: `total(items)`

**The function throws on every input, including the one case it was written for.** It never returns a number.

Measured with Node, not reasoned about:

```
normal  [{price:100,qty:2},{price:50,qty:1}] => THREW TypeError: Cannot read properties of undefined (reading 'price')
empty   []                                   => THREW TypeError: Cannot read properties of undefined (reading 'price')
single  [{price:100,qty:1}]                   => THREW TypeError: Cannot read properties of undefined (reading 'price')
```

There is no input on which this code works, so everything below the first defect is blocked behind it.

---

## Defects, in order of severity

### 1. Off-by-one in the loop bound — the fatal defect

```js
for (let i = 0; i <= items.length; i++)
```

The last valid index is `items.length - 1`. `i <= items.length` runs one iteration past the end, where
`items[i]` is `undefined`, and reading `undefined.price` throws.

This is the `<=` / `<` defect: the loop was written to include the end index and included one too many.

The function does not work even on its happy path. Fix first:

```js
for (let i = 0; i < items.length; i++)
```

Or remove the index entirely, which also removes the chance of repeating the mistake:

```js
for (const item of items) {
  sum += item.price * item.qty;
}
```

### 2. The function does two jobs, and the name hides the second one

`total` computes a sum **and** writes `items.total = sum`. Two effects, one name.

A caller reading `total(order)` expects a calculation. It cannot see that the argument is mutated. Per the
code's own standard — a name is a label that touches the body — the name is wrong, and the mutation is a
surprise (defect class: mutating an argument).

Split them so each name states one effect:

```js
// Computes the order total in integer kopecks. Does not modify `items`.
function computeTotalKopecks(items) {
  let sum = 0;
  for (const item of items) {
    sum += item.price * item.qty;
  }
  return sum;
}

// Stores the total on the order.
function applyTotal(items) {
  items.total = computeTotalKopecks(items);
}
```

Note the unit in the name. The current name `total` does not say whether it returns rubles or kopecks, and
the body is not consistent about it (see defect 3).

### 3. Unit conversion happens inside the sum; the comment says otherwise

The leading comment is `// Считает суммарную стоимость заказа и сохраняет её.` — "computes the order total and
saves it". But the function returns `sum / 100`, i.e. rubles, while `items.total` is assigned `sum`, i.e.
kopecks. **Two different units leave this one function**, and neither name says which one.

The comment and the code disagree about what is saved. One unit must be chosen and named:

```js
// Integer kopecks on the wire: money is never a float.
function computeTotalKopecks(items) { /* ... */ }
function toRubles(kopecks) { return kopecks / 100; }
```

Rubles as a float is acceptable **only** at the display boundary. Keeping money as an integer (kopecks) inside
the domain avoids the float rounding that loses a kopeck on large orders. This is the one place the review
spends correctness budget fully, because it is money.

### 4. No handling of `null`, `undefined`, or a missing `items`

`total(undefined)` and `total(null)` throw a `TypeError` from `items.length`, which is a worse message than
the caller deserves. State the contract: either guard, or document that `items` must be an array.

### 5. Missing or non-numeric fields are accepted silently

If any item has no `price` and no `qty`, or has them as strings (`"100"`), the multiplication produces `NaN`,
`sum` becomes `NaN`, and the function returns `NaN` with no error. Money silently becomes `NaN`.

Decide the contract and enforce it: reject the item with a message that names the offending index and field,
rather than returning poison.

---

## Suggested rewrite

```js
// Computes the total in integer kopecks, then stores it on the order.
// Returns rubles for display; the stored value stays in kopecks to avoid float rounding.
function total(items) {
  if (!Array.isArray(items)) {
    throw new TypeError('total(items): expected an array, got ' + typeof items);
  }

  let kopecks = 0;
  for (const item of items) {
    if (typeof item.price !== 'number' || typeof item.qty !== 'number') {
      throw new TypeError('total(items): item.price and item.qty must be numbers');
    }
    kopecks += item.price * item.qty;
  }

  items.total = kopecks;
  return kopecks / 100;
}
```

The loop bound is gone (no off-by-one possible). The unit is named in the variable (`kopecks`), not in a
trailing comment. The bad inputs fail with a message that says which value was wrong.

---

## The comment, re-checked

Two comments survive the four-question check:

- `// сохраняем итог в объект` (`// save the total into the object`) — **delete.** The code `items.total = sum`
  already says "assign the total field". The comment restates the line. Per rule 13, delete it and make the
  name do the work.
- The header comment — keep, but it must match the fixed behavior. As written it misdescribes the units.

---

## What I checked

- **Loop bound** → `<=` reads one past the end → throws on every input. Confirmed by running the function.
- **Empty array** → throws (index `0` is `undefined`). Should return `0`.
- **Single item** → throws. Should return that item's line total.
- **Mutation of the argument** → `items.total` is written; the name `total` does not announce it.
- **Units** → returns rubles, stores kopecks; comment and code disagree; names say neither.
- **`null` / non-array `items`** → throws from `items.length`.
- **Non-numeric `price`/`qty`** → silently yields `NaN`, no error.

## Left as is (deliberate)

- The style of the surrounding file (single `function`, no module wrapper) — kept, per "consistency beats
  taste". Rewrite changes behavior and clarity, not the file's conventions.
- Did not add a rounding choice for the ruble return — that is a product decision (round, floor, or throw on
  remainders); the fix keeps the exact division until a rule is chosen.

## Next action

Replace the loop bound `i <= items.length` with `i < items.length`, then re-run the three cases above; all
three should stop throwing.
