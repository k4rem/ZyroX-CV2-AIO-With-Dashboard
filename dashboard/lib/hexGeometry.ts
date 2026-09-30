/** Pointy-top hexagon helpers (30° geometry, shared by HexLoader and Perimeter). */

export type Point = [number, number];

/** Vertices of a pointy-top hexagon centred at (cx, cy) with circumradius r. */
export function hexVertices(cx: number, cy: number, r: number): Point[] {
  const out: Point[] = [];
  for (let i = 0; i < 6; i++) {
    const angle = (Math.PI / 180) * (60 * i - 90);
    out.push([cx + r * Math.cos(angle), cy + r * Math.sin(angle)]);
  }
  return out;
}

/** One edge segment with cut gaps at both ends (logo-style breaks). */
export function hexEdgeSegment(vertices: Point[], index: number, gap = 0.03): string {
  const [x1, y1] = vertices[index];
  const [x2, y2] = vertices[(index + 1) % 6];
  const ax = x1 + (x2 - x1) * gap;
  const ay = y1 + (y2 - y1) * gap;
  const bx = x2 - (x2 - x1) * gap;
  const by = y2 - (y2 - y1) * gap;
  return `M${ax.toFixed(2)} ${ay.toFixed(2)}L${bx.toFixed(2)} ${by.toFixed(2)}`;
}

/** Label anchor just outside a vertex, along the outward normal. */
export function hexLabelAnchor(vertices: Point[], index: number, offset: number): Point {
  const [x, y] = vertices[index];
  const cx = vertices.reduce((s, p) => s + p[0], 0) / 6;
  const cy = vertices.reduce((s, p) => s + p[1], 0) / 6;
  const dx = x - cx;
  const dy = y - cy;
  const len = Math.hypot(dx, dy) || 1;
  return [x + (dx / len) * offset, y + (dy / len) * offset];
}
