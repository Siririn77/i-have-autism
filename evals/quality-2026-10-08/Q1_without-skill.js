'use strict';

/**
 * In-memory per-user rate limiter with a rolling 60-second window.
 *
 * Design: a sliding-window log. Each user has a deque of request timestamps
 * recorded in the current window. `check(userId)` first evicts timestamps that
 * have fallen out of the window, then admits the request if fewer than `limit`
 * timestamps remain.
 *
 * The clock is injectable so behaviour is deterministic under test.
 */

const DEFAULT_WINDOW_MS = 60_000;
const DEFAULT_LIMIT = 60;

class RateLimiter {
  /**
   * @param {object} [options]
   * @param {number} [options.limit=60]      Max requests allowed per window.
   * @param {number} [options.windowMs=60000] Rolling window length in ms.
   * @param {() => number} [options.now]     Clock, defaults to Date.now.
   */
  constructor(options = {}) {
    const { limit = DEFAULT_LIMIT, windowMs = DEFAULT_WINDOW_MS } = options;
    if (!Number.isInteger(limit) || limit < 0) {
      throw new RangeError('limit must be a non-negative integer');
    }
    if (!Number.isFinite(windowMs) || windowMs <= 0) {
      throw new RangeError('windowMs must be a positive number');
    }
    this.limit = limit;
    this.windowMs = windowMs;
    this.now = typeof options.now === 'function' ? options.now : Date.now;
    /** @type {Map<string, number[]>} userId -> ascending timestamps */
    this.buckets = new Map();
  }

  /**
   * Record a request and report whether it is allowed.
   * Side effect: an allowed request consumes a slot; a rejected one does not.
   * @param {string} userId
   * @returns {boolean}
   */
  check(userId) {
    if (typeof userId !== 'string' || userId.length === 0) {
      throw new TypeError('userId must be a non-empty string');
    }
    const ts = this.now();
    const cutoff = ts - this.windowMs;

    let hits = this.buckets.get(userId);
    if (hits === undefined) {
      hits = [];
      this.buckets.set(userId, hits);
    }

    // Evict timestamps that have slid out of the window. Because timestamps are
    // appended in non-decreasing order, we can drop a prefix in O(k) after seek.
    let drop = 0;
    while (drop < hits.length && hits[drop] <= cutoff) drop++;
    if (drop > 0) hits.splice(0, drop);

    if (hits.length >= this.limit) {
      return false;
    }
    hits.push(ts);
    return true;
  }

  /** Remaining allowed requests for a user right now. */
  remaining(userId) {
    const hits = this.buckets.get(userId);
    if (hits === undefined) return this.limit;
    const cutoff = this.now() - this.windowMs;
    let drop = 0;
    while (drop < hits.length && hits[drop] <= cutoff) drop++;
    return Math.max(0, this.limit - (hits.length - drop));
  }

  /** Forget all state for a user (e.g. on logout). */
  reset(userId) {
    this.buckets.delete(userId);
  }

  /** Drop empty/dead buckets so memory does not grow with idle users. */
  prune() {
    const cutoff = this.now() - this.windowMs;
    for (const [userId, hits] of this.buckets) {
      let drop = 0;
      while (drop < hits.length && hits[drop] <= cutoff) drop++;
      if (drop > 0) hits.splice(0, drop);
      if (hits.length === 0) this.buckets.delete(userId);
    }
  }
}

/** Convenience factory. */
function createRateLimiter(options) {
  return new RateLimiter(options);
}

module.exports = { RateLimiter, createRateLimiter, DEFAULT_LIMIT, DEFAULT_WINDOW_MS };
