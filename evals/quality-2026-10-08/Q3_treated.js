// Unit name -> length in seconds. This one table is the whole definition of a
// unit: toSeconds converts with it and UNITS is built from it, so a unit is
// added or corrected here and nowhere else.
const SECONDS_PER_UNIT = {
  day: 86400,
  hour: 3600,
  minute: 60,
};

// `start` and `seconds` hold the same quantity by definition, so both are built
// from the single value above and cannot drift apart. `start` is kept because
// existing callers read it; dropping it would change what this module exports.
const UNITS = Object.values(SECONDS_PER_UNIT).map((seconds) => ({
  start: seconds,
  seconds,
}));

/**
 * Converts `value` from the named unit to seconds.
 * An unknown or missing unit returns `value` unchanged.
 *
 * @param {number} value Amount expressed in `unit`.
 * @param {string} unit One of the keys of the unit table above.
 * @returns {number} `value` in seconds, or `value` if `unit` is not known.
 */
function toSeconds(value, unit) {
  if (!Object.hasOwn(SECONDS_PER_UNIT, unit)) return value;
  return value * SECONDS_PER_UNIT[unit];
}

module.exports = { UNITS, toSeconds };
