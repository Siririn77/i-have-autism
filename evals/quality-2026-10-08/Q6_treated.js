'use strict';

/**
 * Money — an exact currency amount, held as an integer count of minor units.
 *
 * Minor units are the smallest indivisible part of a currency: cents for USD,
 * pence for GBP, whole yen for JPY. The amount is always an integer, never a
 * float.
 *
 * Why not a float: 0.1 + 0.2 === 0.30000000000000004, so a cent can appear or
 * vanish as prices are summed. Integers over minor units are exact, and that
 * exactness is enforced at the boundary — every entry point throws on a value
 * that is not a safe integer instead of rounding it silently.
 *
 * Amounts in different currencies never combine: `add` throws on a mismatch
 * rather than guessing a conversion rate. Amounts may be negative (a refund, a
 * balance owed); quantities in `multiply` may not.
 */
class Money {
  /**
   * @param {number} minorUnits  Integer count of minor units (e.g. cents).
   *                             May be negative. Must be a safe integer.
   * @param {string} currency    ISO 4217 code, e.g. 'USD'. Case-sensitive.
   * @throws {TypeError} if either argument is malformed.
   */
  constructor(minorUnits, currency) {
    this.minorUnits = requireMinorUnitCount(minorUnits, 'minorUnits');
    this.currency = requireCurrency(currency);
    Object.freeze(this);
  }

  /**
   * Add another amount of the same currency.
   *
   * @param {Money} other
   * @returns {Money} a new amount; neither operand is modified.
   * @throws {TypeError} if `other` is not Money, or the currencies differ.
   */
  add(other) {
    requireMoney(other, 'other');
    requireSameCurrency(this, other);
    requireExactSum(this.minorUnits, other.minorUnits, 'add');
    return new Money(this.minorUnits + other.minorUnits, this.currency);
  }

  /**
   * Multiply this amount by a whole quantity (for example, 5 identical items).
   *
   * A fractional quantity is refused on purpose: the exact product would not be
   * a whole number of minor units, and choosing a rounding rule here would
   * decide a money question in secret. Round where the business rule that owns
   * rounding lives, then pass the whole number in.
   *
   * @param {number} quantity  A non-negative safe integer.
   * @returns {Money} a new amount; this amount is not modified.
   * @throws {RangeError} if `quantity` is negative, fractional, or not finite.
   */
  multiply(quantity) {
    if (!Number.isSafeInteger(quantity) || quantity < 0) {
      throw new RangeError(
        `quantity must be a non-negative safe integer, got ${String(quantity)}`
      );
    }
    requireExactSpan(this.minorUnits, quantity);
    return new Money(this.minorUnits * quantity, this.currency);
  }
}

/** Throws unless `value` is a safe integer, and returns it unchanged. */
function requireMinorUnitCount(value, label) {
  if (!Number.isSafeInteger(value)) {
    throw new TypeError(
      `${label} must be a safe integer of minor units, got ${String(value)}`
    );
  }
  return value;
}

/** Throws unless `value` is a non-empty string, and returns it unchanged. */
function requireCurrency(value) {
  if (typeof value !== 'string' || value.length === 0) {
    throw new TypeError(`currency must be a non-empty string, got ${String(value)}`);
  }
  return value;
}

/** Throws unless `value` is a Money instance. */
function requireMoney(value, label) {
  if (!(value instanceof Money)) {
    throw new TypeError(`${label} must be a Money instance, got ${String(value)}`);
  }
}

/**
 * Reject a sum that would land outside the safe integer range, where `+`
 * silently rounds — so the error names overflow, not a malformed result.
 */
function requireExactSum(a, b, label) {
  const sum = a + b;
  if (!Number.isSafeInteger(sum)) {
    throw new RangeError(`${label} overflows the safe integer range`);
  }
}

/** Reject a product that would land outside the exactly-representable range. */
function requireExactSpan(minorUnits, quantity) {
  const product = minorUnits * quantity;
  if (!Number.isSafeInteger(product)) {
    throw new RangeError('multiply overflows the safe integer range');
  }
}

/** Throws unless both amounts share one currency. */
function requireSameCurrency(left, right) {
  if (left.currency !== right.currency) {
    throw new TypeError(
      `cannot combine ${left.currency} with ${right.currency}`
    );
  }
}

module.exports = { Money };
