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

/** Midpoint of hex edge `index`. */
export function hexEdgeMidpoint(vertices: Point[], index: number): Point {
  const [x1, y1] = vertices[index];
  const [x2, y2] = vertices[(index + 1) % 6];
  return [(x1 + x2) / 2, (y1 + y2) / 2];
}

/** Outward unit normal from centre through the edge midpoint. */
export function hexEdgeOutwardNormal(vertices: Point[], index: number, cx: number, cy: number): Point {
  const [mx, my] = hexEdgeMidpoint(vertices, index);
  const dx = mx - cx;
  const dy = my - cy;
  const len = Math.hypot(dx, dy) || 1;
  return [dx / len, dy / len];
}

/** Short tick mark on a ring, tangent to the hex edge at its midpoint. */
export function hexEdgeTick(
  vertices: Point[],
  index: number,
  cx: number,
  cy: number,
  tickHalf = 3,
): string {
  const [mx, my] = hexEdgeMidpoint(vertices, index);
  const [x1, y1] = vertices[index];
  const [x2, y2] = vertices[(index + 1) % 6];
  const tx = x2 - x1;
  const ty = y2 - y1;
  const tlen = Math.hypot(tx, ty) || 1;
  const ux = tx / tlen;
  const uy = ty / tlen;
  return `M${(mx - ux * tickHalf).toFixed(2)} ${(my - uy * tickHalf).toFixed(2)}L${(mx + ux * tickHalf).toFixed(2)} ${(my + uy * tickHalf).toFixed(2)}`;
}
