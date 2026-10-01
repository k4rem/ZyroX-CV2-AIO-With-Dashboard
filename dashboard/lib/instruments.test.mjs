import test from "node:test";
import assert from "node:assert/strict";
import {
  LATENCY_CAPACITY,
  appendLatencySample,
  cutSlantDeg,
  latencyStats,
  polar,
  polylinePath,
  ringSegments,
  segmentPath,
  sparklinePoints,
  tickPath,
} from "./instruments.ts";

const NUMERIC_PATH = /^[MLAZ0-9 .,-]*$/;
const ring = { cx: 50, cy: 50, r: 40, width: 8, gapDeg: 3 };

test("latency buffer is bounded to the capacity and keeps the newest samples", () => {
  let buf = [];
  for (let i = 0; i < 50; i++) buf = appendLatencySample(buf, { at: i, ms: 100 + i });
  assert.equal(buf.length, LATENCY_CAPACITY);
  assert.equal(buf[0].at, 50 - LATENCY_CAPACITY);
  assert.equal(buf[buf.length - 1].ms, 149);
});

test("latency buffer does not mutate its input and respects a custom capacity", () => {
  const start = [{ at: 1, ms: 10 }];
  const next = appendLatencySample(start, { at: 2, ms: 20 }, 1);
  assert.deepEqual(start, [{ at: 1, ms: 10 }]);
  assert.deepEqual(next, [{ at: 2, ms: 20 }]);
});

test("latency buffer rejects NaN, infinite and negative readings and rounds ms", () => {
  let buf = [];
  for (const ms of [NaN, Infinity, -5, null, undefined]) buf = appendLatencySample(buf, { at: 1, ms });
  assert.equal(buf.length, 0);
  buf = appendLatencySample(buf, { at: 2, ms: 157.6 });
  assert.deepEqual(buf, [{ at: 2, ms: 158 }]);
});

test("latency stats: empty, then min/max/latest", () => {
  assert.deepEqual(latencyStats([]), { count: 0, latest: null, min: null, max: null });
  const s = latencyStats([
    { at: 1, ms: 160 },
    { at: 2, ms: 140 },
    { at: 3, ms: 152 },
  ]);
  assert.deepEqual(s, { count: 3, latest: 152, min: 140, max: 160 });
});

test("sparkline: invalid sizes and empty buffers produce no points", () => {
  const one = [{ at: 1, ms: 100 }];
  assert.deepEqual(sparklinePoints([], { width: 200, height: 60 }), []);
  assert.deepEqual(sparklinePoints(one, { width: 0, height: 60 }), []);
  assert.deepEqual(sparklinePoints(one, { width: NaN, height: 60 }), []);
  assert.deepEqual(sparklinePoints(one, { width: 200, height: -1 }), []);
});

test("sparkline: a flat series sits on the vertical centre and every coordinate is finite", () => {
  const buf = [1, 2, 3, 4].map((at) => ({ at, ms: 150 }));
  const pts = sparklinePoints(buf, { width: 200, height: 60 });
  assert.equal(pts.length, 4);
  for (const p of pts) {
    assert.ok(Number.isFinite(p.x) && Number.isFinite(p.y));
    assert.equal(p.y, 30);
  }
});

test("sparkline: slots fill left to right so the line extends; higher latency is drawn higher", () => {
  const buf = [
    { at: 1, ms: 100 },
    { at: 2, ms: 200 },
  ];
  const pts = sparklinePoints(buf, { width: 190, height: 60, capacity: 20 });
  assert.equal(pts[0].x, 0);
  assert.ok(pts[1].x > pts[0].x && pts[1].x < 190, "second sample is not stretched to the far edge");
  assert.ok(pts[1].y < pts[0].y);
  assert.match(polylinePath(pts), /^M[\d.]+ [\d.]+ L[\d.]+ [\d.]+$/);
  assert.equal(polylinePath([]), "");
});

test("ring segments: zero, negative or NaN counts draw nothing", () => {
  assert.deepEqual(ringSegments(0, ring), []);
  assert.deepEqual(ringSegments(-3, ring), []);
  assert.deepEqual(ringSegments(NaN, ring), []);
  assert.deepEqual(ringSegments(4, { ...ring, r: NaN }), []);
});

test("ring segments: one path per item, numeric only, ordered clockwise", () => {
  const segs = ringSegments(6, { ...ring, slantDeg: cutSlantDeg(8, 40) });
  assert.equal(segs.length, 6);
  for (const s of segs) {
    assert.match(s.d, NUMERIC_PATH);
    assert.ok(!s.d.includes("NaN"));
  }
  for (let i = 1; i < segs.length; i++) assert.ok(segs[i].midDeg > segs[i - 1].midDeg);
});

test("ring segments: a single item still draws a closed arc", () => {
  const [only] = ringSegments(1, ring);
  assert.ok(only.d.length > 0);
  assert.ok(!only.d.includes("NaN"));
});

test("ring segments: very large counts cap at 360 and shrink the gap instead of vanishing", () => {
  const segs = ringSegments(1000, ring);
  assert.equal(segs.length, 360);
  for (const s of segs) assert.ok(!s.d.includes("NaN"));
});

test("segment and tick paths reject invalid input instead of emitting NaN", () => {
  assert.equal(segmentPath(ring, NaN, 10), "");
  assert.equal(segmentPath({ ...ring, width: 0 }, 0, 10), "");
  assert.equal(segmentPath({ ...ring, width: 80 }, 0, 10), "");
  assert.ok(!tickPath(50, 50, 40, 44, [0, 90, NaN]).includes("NaN"));
});

test("cut slant: 30° geometry, zero for invalid bands; polar uses 12 o'clock as 0°", () => {
  assert.ok(Math.abs(cutSlantDeg(10, 100) - (10 * Math.tan(Math.PI / 6) / 100) * (180 / Math.PI)) < 1e-9);
  assert.equal(cutSlantDeg(0, 100), 0);
  assert.equal(cutSlantDeg(10, NaN), 0);
  const top = polar(50, 50, 10, 0);
  assert.ok(Math.abs(top.x - 50) < 1e-9 && Math.abs(top.y - 40) < 1e-9);
});
