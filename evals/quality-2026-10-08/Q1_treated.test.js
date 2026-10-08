'use strict';

const test = require('node:test');
const assert = require('node:assert/strict');
const { createRateLimiter } = require('./Q1_treated.js');

// Controllable clock: tests advance time by hand, so no real waiting is needed.
function makeClock(start = 0) {
  let current = start;
  return {
    now: () => current,
    advance(ms) {
      current += ms;
    },
  };
}

test('allows up to the limit, then rejects', () => {
  const clock = makeClock();
  const limiter = createRateLimiter({ limit: 3, now: clock.now });
  assert.equal(limiter.check('u'), true);
  assert.equal(limiter.check('u'), true);
  assert.equal(limiter.check('u'), true);
  assert.equal(limiter.check('u'), false);
  assert.equal(limiter.check('u'), false);
});

test('the window rolls: oldest requests expire one at a time', () => {
  const clock = makeClock();
  const limiter = createRateLimiter({ limit: 2, windowMs: 1000, now: clock.now });
  assert.equal(limiter.check('u'), true); // t=0
  clock.advance(400);
  assert.equal(limiter.check('u'), true); // t=400
  assert.equal(limiter.check('u'), false); // t=400, two live

  clock.advance(601); // t=1001: the t=0 request leaves the (t=1, t=1001] window
  assert.equal(limiter.check('u'), true);
});

test('a request exactly windowMs old has expired (open window edge)', () => {
  const clock = makeClock();
  const limiter = createRateLimiter({ limit: 1, windowMs: 1000, now: clock.now });
  assert.equal(limiter.check('u'), true);
  clock.advance(1000);
  assert.equal(limiter.check('u'), true); // age is exactly 1000, not < 1000
});

test('a rejected request does not consume future allowance', () => {
  const clock = makeClock();
  const limiter = createRateLimiter({ limit: 1, windowMs: 1000, now: clock.now });
  assert.equal(limiter.check('u'), true);
  clock.advance(10);
  assert.equal(limiter.check('u'), false);
  clock.advance(991); // t=1001, first request gone
  assert.equal(limiter.check('u'), true);
});

test('users are independent', () => {
  const limiter = createRateLimiter({ limit: 1, now: () => 0 });
  assert.equal(limiter.check('a'), true);
  assert.equal(limiter.check('b'), true);
  assert.equal(limiter.check('a'), false);
  assert.equal(limiter.check('b'), false);
});

test('rejects malformed construction', () => {
  assert.throws(() => createRateLimiter({ limit: 0 }), TypeError);
  assert.throws(() => createRateLimiter({ limit: 2.5 }), TypeError);
  assert.throws(() => createRateLimiter({ limit: undefined }), TypeError);
  assert.throws(() => createRateLimiter({ limit: 1, windowMs: -5 }), TypeError);
  assert.throws(() => createRateLimiter({ limit: 1, now: 'clock' }), TypeError);
});

test('rejects a non-string or empty userId', () => {
  const limiter = createRateLimiter({ limit: 1, now: () => 0 });
  for (const bad of [null, undefined, '', 42, {}, []]) {
    assert.throws(() => limiter.check(bad), TypeError);
  }
});

test('a clock returning a non-finite number is a loud failure, not a silent bypass', () => {
  for (const bad of [NaN, Infinity, '0', null]) {
    const limiter = createRateLimiter({ limit: 1, now: () => bad });
    assert.throws(() => limiter.check('u'), TypeError);
  }
});
