import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Indeterminate loader (DS §12.4): a pointy-top hexagon cut into six segments
 * that light in sequence. Geometry echoes the CLS mark's 30° strokes and cut gaps.
 * Replaces every spinning RefreshCw loader. Reduced motion renders it static.
 */

// Pointy-top hexagon, centre (12,12), radius 9.
const VERTICES: [number, number][] = [
  [12, 3],
  [19.79, 7.5],
  [19.79, 16.5],
  [12, 21],
  [4.21, 16.5],
  [4.21, 7.5],
];

const GAP = 0.14; // fraction of each edge cut away at both ends

function segment(i: number) {
  const [x1, y1] = VERTICES[i];
  const [x2, y2] = VERTICES[(i + 1) % VERTICES.length];
  const ax = x1 + (x2 - x1) * GAP;
  const ay = y1 + (y2 - y1) * GAP;
  const bx = x2 - (x2 - x1) * GAP;
  const by = y2 - (y2 - y1) * GAP;
  return `M${ax.toFixed(2)} ${ay.toFixed(2)}L${bx.toFixed(2)} ${by.toFixed(2)}`;
}

export interface HexLoaderProps extends React.SVGAttributes<SVGSVGElement> {
  size?: 14 | 16 | 24;
  label?: string;
}

export function HexLoader({ size = 16, label = "Loading", className, ...props }: HexLoaderProps) {
  return (
    <span role="status" className="inline-flex shrink-0">
      <svg
        viewBox="0 0 24 24"
        width={size}
        height={size}
        fill="none"
        stroke="currentColor"
        strokeWidth={2}
        strokeLinecap="butt"
        aria-hidden="true"
        className={cn("text-brand-400", className)}
        {...props}
      >
        {VERTICES.map((_, i) => (
          <path
            key={i}
            d={segment(i)}
            className="cls-hex-seg"
            style={{ animationDelay: `${i * 120}ms` }}
          />
        ))}
      </svg>
      <span className="sr-only">{label}</span>
    </span>
  );
}
