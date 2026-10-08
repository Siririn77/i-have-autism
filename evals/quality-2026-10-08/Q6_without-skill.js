/**
 * Q6_without-skill.js — a small `Money` helper for currency amounts.
 *
 * Amounts are stored as an integer number of minor units (cents). All
 * arithmetic is performed on those integers, so `Money` avoids the classic
 * floating-point drift you get from doing math on `0.1 + 0.2`-style dollar
 * values. `0.10 + 0.20` in dollars is `0.30000000000000004`; in cents it is
 * exactly `30`.
 *
 * Design notes:
 *  - Immutable: every operation returns a new `Money`; instances are never
 *    mutated in place.
 *  - Currency-aware: you may attach an ISO 4217 code (default `"USD"`).
 *    Adding or comparing across differing currencies throws, rather than
 *    silently producing a wrong number.
 *  - Integer-safe: constructors and multipliers reject non-integer minor
 *    units and non-integer quantities, and reject values outside the range
 *    that can be represented exactly as a Number.
 *
 * @module Money
 */

"use strict";

/** Largest integer that is exactly representable as a JS Number (2^53 - 1). */
const MAX_SAFE = Number.MAX_SAFE_INTEGER;

/**
 * Assert that a value is a safe integer, optionally within [min, max].
 * @param {unknown} value
 * @param {string} label human-readable name for the error message
 * @param {number} [min]
 * @param {number} [max]
 * @returns {number} the validated value
 */
function assertSafeInteger(value, label, min = -MAX_SAFE, max = MAX_SAFE) {
  if (typeof value !== "number" || !Number.isInteger(value)) {
    throw new TypeError(`${label} must be an integer, received ${describe(value)}`);
  }
  if (value < min || value > max) {
    throw new RangeError(
      `${label} must be between ${min} and ${max}, received ${value}`
    );
  }
  return value;
}

/**
 * Render an arbitrary value for an error message.
 * @param {unknown} value
 * @returns {string}
 */
function describe(value) {
  if (typeof value === "string") return JSON.stringify(value);
  if (value === null) return "null";
  if (typeof value === "object") return Object.prototype.toString.call(value);
  return String(value);
}

/**
 * A currency amount held as an integer count of minor units.
 *
 * @example
 * const a = Money.fromCents(1099);        // $10.99
 * const b = Money.fromCents(250);         // $2.50
 * a.add(b).format();                      // "$13.49"
 * a.multiply(3).format();                 // "$32.97"
 */
class Money {
  /**
   * @param {number} amount integer count of minor units (cents)
   * @param {string} [currency] ISO 4217 code, default "USD"
   */
  constructor(amount, currency = "USD") {
    this.amount = assertSafeInteger(amount, "amount");
    this.currency = normalizeCurrency(currency);
    Object.freeze(this);
  }

  /**
   * Build from an integer number of minor units (cents).
   * @param {number} cents
   * @param {string} [currency]
   * @returns {Money}
   */
  static fromCents(cents, currency = "USD") {
    return new Money(cents, currency);
  }

  /**
   * Build from a major-unit amount (e.g. dollars). The value is rounded to
   * the nearest minor unit; pass `{ exact: true }` to reject amounts that do
   * not land precisely on a minor unit.
   *
   * @param {number} value e.g. 10.99
   * @param {string} [currency]
   * @param {{exact?: boolean}} [options]
   * @returns {Money}
   */
  static fromMajor(value, currency = "USD", options = {}) {
    if (typeof value !== "number" || !Number.isFinite(value)) {
      throw new TypeError(`value must be a finite number, received ${describe(value)}`);
    }
    const cents = value * 100;
    // Snap tiny float error (e.g. 10.99 * 100 = 1098.9999999999998) before
    // deciding whether the input is exact.
    const rounded = Math.round(cents);
    const isExact = Math.abs(cents - rounded) < 1e-6;
    if (options.exact && !isExact) {
      throw new RangeError(`${value} is not an exact number of minor units`);
    }
    return new Money(rounded, currency);
  }

  /**
   * The number of minor units (cents) as an integer.
   * @returns {number}
   */
  get cents() {
    return this.amount;
  }

  /**
   * Sum this amount with one or more others of the same currency.
   * @param {...Money} others
   * @returns {Money} a new instance
   */
  add(...others) {
    const [left, right] = this._merge(others);
    return new Money(left + right, this.currency);
  }

  /**
   * Subtract one or more same-currency amounts from this one.
   * @param {...Money} others
   * @returns {Money} a new instance
   */
  subtract(...others) {
    const [left, right] = this._merge(others);
    return new Money(left - right, this.currency);
  }

  /**
   * Multiply this amount by a quantity (piece count, months, etc.).
   * The quantity must be an integer: half a cent item multiplied by 0.5 is
   * not representable, so it is rejected rather than rounded silently.
   *
   * @param {number} quantity non-negative safe integer
   * @returns {Money} a new instance
   */
  multiply(quantity) {
    if (typeof quantity !== "number" || !Number.isInteger(quantity)) {
      throw new TypeError(`quantity must be an integer, received ${describe(quantity)}`);
    }
    if (quantity < 0) {
      throw new RangeError(`quantity must be non-negative, received ${quantity}`);
    }
    return new Money(this.amount * quantity, this.currency);
  }

  /**
   * Add a same-currency amount zero or more times, i.e. `add(other).multiply(n)`
   * collapsed into one allocation.
   * @param {Money} other
   * @param {number} quantity
   * @returns {Money}
   */
  addTimes(other, quantity) {
    const total = this.add(other); // validates currency
    return total.multiply(quantity);
  }

  /**
   * Compare against another amount of the same currency.
   * @param {Money} other
   * @returns {-1|0|1}
   */
  compare(other) {
    const value = this._coerce(other);
    if (this.amount < value) return -1;
    if (this.amount > value) return 1;
    return 0;
  }

  /**
   * @param {Money} other
   * @returns {boolean}
   */
  equals(other) {
    return this.currency === this._coerceCurrency(other) && this.amount === other.amount;
  }

  /** @returns {boolean} */
  isZero() {
    return this.amount === 0;
  }

  /** @returns {boolean} */
  isNegative() {
    return this.amount < 0;
  }

  /**
   * The amount as a major-unit number (e.g. dollars). Subject to the usual
   * float limitations of the target value.
   * @returns {number}
   */
  toMajor() {
    return this.amount / 100;
  }

  /**
   * Format the amount for display.
   *
   * @param {{symbol?: boolean, minimumFractionDigits?: number}} [options]
   * @returns {string} e.g. "$13.49", or "-$13.49" when negative
   */
  format(options = {}) {
    const { symbol = false, minimumFractionDigits = 2 } = options;
    const sign = this.amount < 0 ? "-" : "";
    const abs = Math.abs(this.amount);
    const major = Math.trunc(abs / 100);
    const minor = abs % 100;
    const body =
      `${major}.` +
      String(minor).padStart(2, "0").slice(0, Math.max(2, minimumFractionDigits));
    return `${sign}${symbol ? currencySymbol(this.currency) : ""}${body}`;
  }

  /**
   * Serialize to a plain object.
   * @returns {{amount: number, currency: string}}
   */
  toJSON() {
    return { amount: this.amount, currency: this.currency };
  }

  /**
   * Sum a list of same-currency amounts.
   * @param {Money[]} amounts
   * @returns {Money}
   */
  static sum(amounts) {
    if (!Array.isArray(amounts)) {
      throw new TypeError("sum expects an array of Money instances");
    }
    let total = null;
    for (const item of amounts) {
      if (!(item instanceof Money)) {
        throw new TypeError(`expected a Money instance, received ${describe(item)}`);
      }
      total = total === null ? item : total.add(item);
    }
    return total === null ? new Money(0) : total;
  }

  /**
   * Shared guard for binary operations: return [left, right] minor units
   * after checking currencies match.
   * @param {Money[]} others
   * @returns {[number, number]}
   * @private
   */
  _merge(others) {
    if (others.length === 0) return [this.amount, 0];
    let right = 0;
    for (const other of others) {
      this._coerceCurrency(other);
      assertSafeInteger(other.amount, "amount");
      right += other.amount;
    }
    assertSafeInteger(right, "sum");
    return [this.amount, right];
  }

  /**
   * Validate that another value is a same-currency Money and return its
   * minor units.
   * @param {unknown} other
   * @returns {number}
   * @private
   */
  _coerce(other) {
    this._coerceCurrency(other);
    return other.amount;
  }

  /**
   * Validate a same-currency Money, returning its currency for convenience.
   * @param {unknown} other
   * @returns {string}
   * @private
   */
  _coerceCurrency(other) {
    if (!(other instanceof Money)) {
      throw new TypeError(`expected a Money instance, received ${describe(other)}`);
    }
    if (other.currency !== this.currency) {
      throw new TypeError(
        `currency mismatch: cannot combine ${this.currency} with ${other.currency}`
      );
    }
    return other.currency;
  }
}

/**
 * Canonicalize a currency code to upper-case.
 * @param {unknown} currency
 * @returns {string}
 */
function normalizeCurrency(currency) {
  if (typeof currency !== "string" || currency.trim() === "") {
    throw new TypeError(`currency must be a non-empty string, received ${describe(currency)}`);
  }
  return currency.trim().toUpperCase();
}

/**
 * Best-effort display symbol for a currency code; falls back to the code.
 * @param {string} currency
 * @returns {string}
 */
function currencySymbol(currency) {
  const symbols = { USD: "$", EUR: "\u20ac", GBP: "\u00a3", JPY: "\u00a5", RUB: "\u20bd" };
  return symbols[currency] || `${currency} `;
}

/**
 * Convenience factory: `money(1099)` === `Money.fromCents(1099)`.
 * @param {number} cents
 * @param {string} [currency]
 * @returns {Money}
 */
function money(cents, currency) {
  return Money.fromCents(cents, currency);
}

export { Money, money };
export default Money;
