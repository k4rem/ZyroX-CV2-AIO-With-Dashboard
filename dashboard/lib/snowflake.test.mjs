import assert from "node:assert/strict";
import test from "node:test";
import {
  compareSnowflakes,
  isSnowflakeString,
  normalizeSnowflakeInput,
  parseCommaSeparatedSnowflakes,
} from "./snowflake.ts";

const ABOVE_2_53 = "100000000000000001";
const REAL_SHAPE = "1543105121804615781";

test("normalizeSnowflakeInput preserves digits above 2^53", () => {
  assert.equal(normalizeSnowflakeInput(ABOVE_2_53), ABOVE_2_53);
  assert.equal(normalizeSnowflakeInput(`  ${REAL_SHAPE}  `), REAL_SHAPE);
});

test("Number() would corrupt — strings do not", () => {
  assert.notEqual(Number(ABOVE_2_53), ABOVE_2_53);
  assert.equal(normalizeSnowflakeInput(ABOVE_2_53), "100000000000000001");
});

test("parseCommaSeparatedSnowflakes", () => {
  assert.deepEqual(parseCommaSeparatedSnowflakes(`${ABOVE_2_53}, ${REAL_SHAPE}`), [
    ABOVE_2_53,
    REAL_SHAPE,
  ]);
});

test("compareSnowflakes", () => {
  assert.ok(compareSnowflakes(REAL_SHAPE, REAL_SHAPE));
  assert.ok(isSnowflakeString(REAL_SHAPE));
});
