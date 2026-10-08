# Code Review: `total(items)`

## Summary

The function has one **critical bug** that makes it throw on every non-empty call, plus a
misleading comment and a questionable side effect. Details below.

```js
// Считает суммарную стоимость заказа и сохраняет её.
function total(items) {
  let sum = 0;
  for (let i = 0; i <= items.length; i++) {
    sum += items[i].price * items[i].qty;
  }
  items.total = sum;      // сохраняем итог в объект
  return sum / 100;       // переводим копейки в рубли
}
```

## 1. Off-by-one error — crashes on every call (critical)

```js
for (let i = 0; i <= items.length; i++)
```

The loop condition uses `<=` instead of `<`. On the final iteration `i === items.length`,
so `items[i]` is `undefined`, and reading `.price` throws:

```
TypeError: Cannot read properties of undefined (reading 'price')
```

This is not a subtle edge case — it fires for **any** array, including a normal
non-empty order. The only input that does not throw is an empty array (loop body
never runs).

**Fix:**

```js
for (let i = 0; i < items.length; i++)
```

or, more idiomatically:

```js
for (const item of items) sum += item.price * item.qty;
```

## 2. Comment does not match behavior

The comment says the function "saves the total" — and it does write `items.total` —
but the *returned* value is `sum / 100`, a different number from what is stored.
A caller reading the comment would reasonably expect the stored and returned values
to be the same unit. The return path silently divides, the stored path does not.

## 3. Unit handling is implicit and undocumented

`return sum / 100` assumes prices are stored in kopecks (minor units). That assumption
is nowhere in the signature or the comment, and there is no handling for floating-point
rounding (`0.1 + 0.2` style artifacts when prices are already decimal, or precision
loss when dividing an integer kopek sum). State the unit contract explicitly, e.g.:

```js
/**
 * @param {Array<{price: number, qty: number}>} items - price in kopecks
 * @returns {number} total in rubles
 */
```

## 4. Mutating the input argument

```js
items.total = sum;      // side effect on the caller's array
```

The function silently mutates its input by attaching a `total` property. This:

- surprises callers who pass an array they do not expect to change;
- is inconsistent — `total` mixes a number into an array of order-line objects;
- breaks any caller that later serializes the array or iterates its properties.

Prefer returning a plain number (the function is named `total`, not `annotate`), or
return an object such as `{ total, currency }` if more than one value is needed.

## 5. Minor robustness notes

- No guard for `null`/`undefined` `items`, or for line items missing `price`/`qty`
  (would produce `NaN` silently).
- No validation that `qty`/`price` are numbers.

## Recommended rewrite

```js
/**
 * Sums line-item costs.
 * @param {Array<{price: number, qty: number}>} items - price in kopecks
 * @returns {number} total in rubles
 */
function total(items) {
  let sum = 0;
  for (const { price, qty } of items) {
    sum += price * qty;
  }
  return sum / 100;   // kopecks -> rubles
}
```

This fixes the crash, removes the input mutation, and makes the units explicit.

## Verification

The off-by-one bug was reproduced locally: calling the original `total` on a
one-element array throws `TypeError: Cannot read properties of undefined
(reading 'price')`. The recommended rewrite returns the correct sum for the same input.
