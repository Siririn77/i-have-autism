/**
 * Total magnitude of the amounts belonging to one user.
 *
 * Every entry whose `uid` matches `userId` contributes the absolute value of
 * its `amt`; entries for any other user contribute nothing. The running total
 * therefore starts at zero and can never go negative.
 *
 * @param {string|number} userId
 *   Compared against each entry's `uid` with loose equality, so the number 1
 *   and the string "1" count as the same user. This loose match is deliberate.
 * @param {Object|Array} entries
 *   A map or array of `{ uid, amt }` entries. Walked with `for...in`, which
 *   also visits inherited enumerable properties; this is deliberate.
 * @returns {number}
 *   The summed magnitude, or 0 when no entry matches `userId`.
 */
function sumAmountsForUser(userId, entries) {
  let total = 0;

  for (const key in entries) {
    const entry = entries[key];

    // Loose `==` is deliberate: it is this module's existing contract, so the
    // number 1 and the string "1" are treated as the same user.
    if (entry.uid != userId) {
      continue;
    }

    total += entry.amt > 0 ? entry.amt : -entry.amt;
  }

  return total;
}

module.exports = { p: sumAmountsForUser };
