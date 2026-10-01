/**
 * Overview instrument deck (Phase 1.6 Task A.1). Pure — covered by node --test.
 *
 * Geometry for the segmented rings and the latency sparkline, plus the bounded
 * session latency buffer. Every function tolerates empty or invalid input and
 * never emits NaN into an SVG path.
 */

// --- Session latency buffer --------------------------------------------------

export interface LatencySample {
  /** Epoch ms the reading was taken. */
  at: number;
  ms: number;
}

/** 20 samples at the shell's 30 s cadence ≈ the last 10 minutes of this session. */
export const LATENCY_CAPACITY = 20;

export function appendLatencySample(
  buffer: readonly LatencySample[],
  sample: LatencySample,
  capacity: number = LATENCY_CAPACITY,
): LatencySample[] {
  if (!Number.isFinite(sample.ms) || sample.ms < 0 || !Number.isFinite(sample.at)) return buffer.slice();
  const cap = Math.max(1, Math.floor(capacity));
  const next = [...buffer, { at: sample.at, ms: Math.round(sample.ms) }];
  return next.length > cap ? next.slice(next.length - cap) : next;
}

export function latencyStats(buffer: readonly LatencySample[]): {
  count: number;
  latest: number | null;
  min: number | null;
  max: number | null;
} {
  if (buffer.length === 0) return { count: 0, latest: null, min: null, max: null };
  let min = Infinity;
  let max = -Infinity;
  for (const s of buffer) {
    if (s.ms < min) min = s.ms;
    if (s.ms > max) max = s.ms;
  }
  return { count: buffer.length, latest: buffer[buffer.length - 1].ms, min, max };
}

export interface SparkPoint {
  x: number;
  y: number;
  ms: number;
  at: number;
}

/**
 * Slot-based x (sample i sits in slot i of `capacity`), so a new sample visibly
 * extends the line until the buffer is full. y is scaled to the observed range
 * with padding; a flat series sits on the vertical centre.
 */
export function sparklinePoints(
  buffer: readonly LatencySample[],
  opts: { width: number; height: number; capacity?: number; padY?: number },
): SparkPoint[] {
  const { width, height } = opts;
  const capacity = Math.max(2, Math.floor(opts.capacity ?? LATENCY_CAPACITY));
  const padY = opts.padY ?? 6;
  if (!(width > 0) || !(height > 0)) return [];
  const samples = buffer.filter((s) => Number.isFinite(s.ms)).slice(-capacity);
  if (samples.length === 0) return [];
  const { min, max } = latencyStats(samples);
  const lo = min ?? 0;
  const span = (max ?? 0) - lo;
  const step = width / (capacity - 1);
  const usable = Math.max(0, height - padY * 2);
  return samples.map((s, i) => ({
    x: round(i * step),
    y: round(span === 0 ? height / 2 : padY + usable - ((s.ms - lo) / span) * usable),
    ms: s.ms,
    at: s.at,
  }));
}

export function polylinePath(points: readonly { x: number; y: number }[]): string {
  if (points.length === 0) return "";
  return points.map((p, i) => `${i === 0 ? "M" : "L"}${p.x} ${p.y}`).join(" ");
}

// --- Segmented rings -----------------------------------------------------------

export interface RingOptions {
  cx: number;
  cy: number;
  /** Outer radius of the band. */
  r: number;
  /** Band thickness. */
  width: number;
  /** Angular gap between segments, degrees. */
  gapDeg?: number;
  /**
   * CLS 30° cut: the outer edge of each segment is rotated this many degrees
   * ahead of the inner edge, so segment ends are slanted, not radial.
   */
  slantDeg?: number;
  /** Where the first segment starts, degrees clockwise from 12 o'clock. */
  startDeg?: number;
  /** Total sweep, degrees (360 = full ring). */
  sweepDeg?: number;
}

/** Angular slant (degrees) that tilts a band's segment ends 30° off radial. */
export function cutSlantDeg(bandWidth: number, radius: number): number {
  if (!(bandWidth > 0) || !(radius > 0)) return 0;
  return ((bandWidth * Math.tan(Math.PI / 6)) / radius) * (180 / Math.PI);
}

function round(n: number): number {
  return Math.round(n * 100) / 100;
}

/** Point at radius r, angle deg clockwise from 12 o'clock. */
export function polar(cx: number, cy: number, r: number, deg: number): { x: number; y: number } {
  const rad = (deg * Math.PI) / 180;
  return { x: round(cx + r * Math.sin(rad)), y: round(cy - r * Math.cos(rad)) };
}

/** One annular segment path from a0 to a1 (degrees) with slanted ends. */
export function segmentPath(o: RingOptions, a0: number, a1: number): string {
  const { cx, cy, r, width } = o;
  const slant = o.slantDeg ?? 0;
  const ri = r - width;
  if (![cx, cy, r, width, a0, a1, slant].every(Number.isFinite) || width <= 0 || ri <= 0 || a1 <= a0) return "";
  const span = a1 - a0;
  const large = span > 180 ? 1 : 0;
  const o0 = polar(cx, cy, r, a0 + slant);
  const o1 = polar(cx, cy, r, a1 + slant);
  const i1 = polar(cx, cy, ri, a1);
  const i0 = polar(cx, cy, ri, a0);
  return [
    `M${o0.x} ${o0.y}`,
    `A${r} ${r} 0 ${large} 1 ${o1.x} ${o1.y}`,
    `L${i1.x} ${i1.y}`,
    `A${ri} ${ri} 0 ${large} 0 ${i0.x} ${i0.y}`,
    "Z",
  ].join(" ");
}

export interface RingSegment {
  index: number;
  d: string;
  /** Angle at the middle of the segment, for ticks and labels. */
  midDeg: number;
  startDeg: number;
  endDeg: number;
}

/** `count` equal segments. Returns [] for a non-positive or non-finite count. */
export function ringSegments(count: number, o: RingOptions): RingSegment[] {
  if (!Number.isFinite(count) || count < 1) return [];
  const n = Math.min(Math.floor(count), 360);
  const sweep = Math.min(360, Math.max(1, o.sweepDeg ?? 360));
  const start = o.startDeg ?? 0;
  const slot = sweep / n;
  const gap = n === 1 && sweep === 360 ? 0 : Math.min(slot / 2, Math.max(0, o.gapDeg ?? 3));
  const segs: RingSegment[] = [];
  for (let i = 0; i < n; i++) {
    const a0 = start + i * slot + gap / 2;
    // A single full-ring segment stops just short of 360° so the arc stays drawable.
    const a1 = start + (i + 1) * slot - (gap === 0 ? 0.01 : gap / 2);
    if (a1 <= a0) continue;
    segs.push({ index: i, d: segmentPath(o, a0, a1), midDeg: round((a0 + a1) / 2), startDeg: round(a0), endDeg: round(a1) });
  }
  return segs.filter((s) => s.d !== "");
}

/** Radial tick marks (short lines) at the given angles. */
export function tickPath(cx: number, cy: number, r0: number, r1: number, angles: readonly number[]): string {
  return angles
    .filter(Number.isFinite)
    .map((a) => {
      const p0 = polar(cx, cy, r0, a);
      const p1 = polar(cx, cy, r1, a);
      return `M${p0.x} ${p0.y} L${p1.x} ${p1.y}`;
    })
    .join(" ");
}
