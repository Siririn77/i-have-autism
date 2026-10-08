const MINUTE = 60;
const HOUR = 60 * MINUTE;
const DAY = 24 * HOUR;

// A unit is defined once: its name and its length in seconds, side by side.
// toSeconds and UNITS both read this table, so adding a unit is one edit.
const SECONDS_PER_UNIT = { day: DAY, hour: HOUR, minute: MINUTE };

// Both fields are built from one value above, so `start` and `seconds` cannot
// drift apart. `start` is kept because existing callers read it.
const UNITS = Object.values(SECONDS_PER_UNIT).map((seconds) => ({
  start: seconds,
  seconds,
}));

/** Converts `value` from `unit` to seconds; an unknown unit returns `value` unchanged. */
function toSeconds(value, unit) {
  if (!Object.hasOwn(SECONDS_PER_UNIT, unit)) return value;
  return value * SECONDS_PER_UNIT[unit];
}

module.exports = { UNITS, toSeconds };
