'use strict';

const SECONDS_PER_UNIT = Object.freeze({
  s: 1,
  m: 60,
  h: 60 * 60,
  d: 60 * 60 * 24,
});

/**
 * Parse a human-readable duration string into a total number of seconds.
 *
 * Input grammar: one or more `<number><unit>` tokens, optionally separated by
 * whitespace. `<unit>` is one of `d`, `h`, `m`, `s` (case-insensitive) and may
 * appear in any order. A number may be a decimal. Tokens may be concatenated
 * (`'1h30m'`). Leading and trailing whitespace is ignored.
 *
 * @param {string} text
 * @returns {number} total seconds. A blank string yields 0.
 * @throws {TypeError} when `text` is not a string, or when it is non-blank and
 *   contains anything that is not a valid `<number><unit>` token
 *   (for example `'1x'`, `'-5m'`, `'5'`, `'1h 5x'`).
 */
function parseDuration(text) {
  if (typeof text !== 'string') {
    throw new TypeError(`parseDuration expected a string, received ${typeof text}`);
  }

  const input = text.trim();

  // Empty and whitespace-only input is a zero-length duration, deliberately not an error:
  // callers treat a missing duration as "no wait", and any other typo still throws rather than reading as 0.
  if (input === '') return 0;

  let totalSeconds = 0;
  let consumedUpTo = 0;
  const tokenPattern = /(\d+(?:\.\d+)?)\s*([dhms])/gi;
  let token;

  while ((token = tokenPattern.exec(input)) !== null) {
    requireOnlyWhitespace(input, consumedUpTo, token.index);
    totalSeconds += Number(token[1]) * SECONDS_PER_UNIT[token[2].toLowerCase()];
    consumedUpTo = tokenPattern.lastIndex;
  }
  requireOnlyWhitespace(input, consumedUpTo, input.length);

  // A number past the double range would sum to Infinity; rejecting it here keeps every returned value a real count of seconds.
  if (!Number.isFinite(totalSeconds)) {
    throw new TypeError(`parseDuration produced a non-finite total (${totalSeconds})`);
  }
  return totalSeconds;
}

/**
 * The scan above finds valid tokens anywhere in the string; every character
 * between and after them must be whitespace, or the input is malformed.
 */
function requireOnlyWhitespace(input, from, to) {
  const skipped = input.slice(from, to);
  if (skipped.trim() !== '') {
    throw new TypeError(`parseDuration could not read "${skipped}" as a duration token`);
  }
}

module.exports = parseDuration;
module.exports.parseDuration = parseDuration;

if (require.main === module) {
  const assert = require('assert');
  assert.strictEqual(parseDuration('1h 30m'), 5400);
  assert.strictEqual(parseDuration('45s'), 45);
  assert.strictEqual(parseDuration('2d'), 172800);
  assert.strictEqual(parseDuration('1d 2h 3m 4s'), 93784);
  assert.strictEqual(parseDuration('1h30m'), 5400);
  assert.strictEqual(parseDuration('30m 1h'), 5400);
  assert.strictEqual(parseDuration('1.5h'), 5400);
  assert.strictEqual(parseDuration('  2d  '), 172800);
  assert.strictEqual(parseDuration(''), 0);
  assert.strictEqual(parseDuration('0s'), 0);
  assert.strictEqual(parseDuration('1h 1h'), 7200);
  assert.throws(() => parseDuration('1x'), TypeError);
  assert.throws(() => parseDuration('-5m'), TypeError);
  assert.throws(() => parseDuration('5'), TypeError);
  assert.throws(() => parseDuration('1h 30'), TypeError);
  assert.throws(() => parseDuration('1h 5x'), TypeError);
  assert.throws(() => parseDuration(null), TypeError);
  assert.throws(() => parseDuration(undefined), TypeError);
  assert.throws(() => parseDuration('9'.repeat(400) + 'd'), TypeError);
  console.log('parseDuration: all checks passed');
}
