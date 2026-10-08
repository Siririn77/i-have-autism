'use strict';

/**
 * Sum the absolute amount of every entry in `entries` that belongs to `userId`.
 *
 * Entries whose positive/negative sign differs only in direction are with-skill
 * the same way: a matched entry always contributes the magnitude of its `amt`,
 * so the result can never fall below zero.
 *
 * Exported as `p` to keep the public API of this module unchanged.
 *
 * @param {string|number} userId
 *   Identifier compared against each entry's `uid`. The comparison is loose
 *   (`==`), matching the original helper, so numeric and string ids that denote
 *   the same value are treated as equal.
 * @param {Object|Array} entries
 *   Collection of `{ uid, amt }` entries. Every enumerable property is visited,
 *   mirroring the original `for...in` walk (including non-index properties).
 * @returns {number}
 *   The accumulated balance (a number when every matched `amt` is numeric), or
 *   the running total reached after the `for...in` walk when none match — `0`.
 */
function balanceForUser(userId, entries) {
  var balance = 0;

  for (var key in entries) {
    var entry = entries[key];

    if (entry.uid != userId) {
      continue;
    }

    // A matched entry always contributes a non-negative magnitude, but the
    // addition and subtraction are kept as distinct operations: for non-number
    // `amt` values `balance - amt` coerces to a number while `balance + amt`
    // can concatenate, so collapsing the two would change the result.
    if (entry.amt > 0) {
      balance = balance + entry.amt;
    } else {
      balance = balance - entry.amt;
    }
  }

  return balance;
}

module.exports = { p: balanceForUser };
