'use strict';

const DEFAULT_WINDOW_MS = 60_000;

/**
 * Creates an in-memory rate limiter. At most `limit` calls to `check` return
 * true for one userId inside any rolling `windowMs` window.
 *
 * @param {object} options
 * @param {number} options.limit  Requests allowed per user per window. Positive integer.
 * @param {number} [options.windowMs=60000]  Window length in milliseconds. Positive integer.
 * @param {() => number} [options.now=Date.now]  Clock source. Injected so tests need no real time.
 * @returns {{ check: (userId: string) => boolean }}
 * @throws {TypeError} If `limit` or `windowMs` is not a positive integer, or `now` is not a function.
 */
function createRateLimiter({ limit, windowMs = DEFAULT_WINDOW_MS, now = Date.now } = {}) {
  requirePositiveInteger('limit', limit);
  requirePositiveInteger('windowMs', windowMs);
  if (typeof now !== 'function') {
    throw new TypeError(`now must be a function, got ${describe(now)}`);
  }

  // One entry per user, holding only the timestamps still inside the window.
  const requestTimesByUser = new Map();

  /**
   * Records one request for userId and reports whether it is allowed.
   * Allowed when the user has fewer than `limit` requests inside the window.
   *
   * @param {string} userId  Non-empty identifier of the requester.
   * @returns {boolean} true if allowed, false if the user is rate-limited.
   * @throws {TypeError} If userId is not a non-empty string.
   */
  function check(userId) {
    if (typeof userId !== 'string' || userId === '') {
      throw new TypeError(`userId must be a non-empty string, got ${describe(userId)}`);
    }

    const currentTime = now();
    if (!Number.isFinite(currentTime)) {
      throw new TypeError(`now() must return a finite number, got ${describe(currentTime)}`);
    }
    const windowStart = currentTime - windowMs;
    const recentTimes = (requestTimesByUser.get(userId) ?? []).filter(
      (time) => time > windowStart,
    );

    const allowed = recentTimes.length < limit;
    if (allowed) recentTimes.push(currentTime);
    requestTimesByUser.set(userId, recentTimes); // the rejected call still refreshes the pruned list
    return allowed;
  }

  return { check };
}

function requirePositiveInteger(name, value) {
  if (!Number.isInteger(value) || value <= 0) {
    throw new TypeError(`${name} must be a positive integer, got ${describe(value)}`);
  }
}

function describe(value) {
  return JSON.stringify(value) ?? String(value);
}

module.exports = { createRateLimiter };
