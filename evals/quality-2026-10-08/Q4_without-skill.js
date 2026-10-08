'use strict';

/**
 * parseDuration(text)
 * Convert a human-readable duration string into a total number of seconds.
 *
 * Supported units:
 *   d = days, h = hours, m = minutes, s = seconds
 *
 * Accepted forms:
 *   '1h 30m' -> 5400
 *   '45s'    -> 45
 *   '2d'     -> 172800
 *   '1d 2h 3m 4s' -> 93784
 *
 * Tokens may be separated by spaces, may be concatenated ('1h30m'), and the
 * units may appear in any order. A bare number with no unit is treated as
 * seconds. Returns 0 for empty/blank input, and NaN for input that contains
 * anything that is not a valid number+unit token.
 *
 * @param {string} text
 * @returns {number} total seconds, or NaN when the input is malformed
 */
function parseDuration(text) {
  if (text === null || text === undefined) return NaN;

  const raw = String(text).trim();
  if (raw === '') return 0;

  const UNIT_SECONDS = {
    d: 24 * 60 * 60,
    h: 60 * 60,
    m: 60,
    s: 1,
  };

  // Match one or more "<number><optional-unit>" tokens. A number may be a
  // decimal. Whitespace between tokens is allowed.
  const tokenRe = /(\d+(?:\.\d+)?)\s*([dhms])?/gi;
  const tokens = [];
  let lastIndex = 0;
  let match;

  while ((match = tokenRe.exec(raw)) !== null) {
    // Reject gaps that contain anything other than whitespace, so garbage
    // like '1h xx' or '--5m' is reported as malformed instead of ignored.
    const gap = raw.slice(lastIndex, match.index);
    if (gap.trim() !== '') return NaN;
    lastIndex = tokenRe.lastIndex;

    const value = Number(match[1]);
    const unit = (match[2] || 's').toLowerCase();
    if (!Number.isFinite(value)) return NaN;

    tokens.push(value * UNIT_SECONDS[unit]);
  }

  // Trailing text after the last token is malformed.
  if (raw.slice(lastIndex).trim() !== '') return NaN;
  if (tokens.length === 0) return NaN;

  return tokens.reduce((sum, seconds) => sum + seconds, 0);
}

module.exports = parseDuration;
module.exports.parseDuration = parseDuration;
