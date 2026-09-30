import * as React from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";

/**
 * The official CLS mark, used as supplied (DS §12.1, D18).
 *
 * `/brand/cls-mark-128.png` and `-512.png` are the owner-provided PNG with the pure-black
 * matte removed and cropped to the mark; nothing is traced, redrawn or recoloured.
 * The untouched original lives at `/brand/cls-logo-official.png`.
 * ASSET FOLLOW-UP: a true vector master from the owner would allow crisp favicons
 * and animation. Until then the mark stays raster.
 *
 * The mark is not an icon and is never tinted, rotated, outlined or placed on purple.
 */

// Intrinsic ratio of the cropped mark (297 × 512).
const RATIO = 297 / 512;

export interface ClsMarkProps {
  /** Rendered height in px. Minimum supported height is 16 (DS §12.1). */
  height?: number;
  className?: string;
  priority?: boolean;
}

export function ClsMark({ height = 20, className, priority }: ClsMarkProps) {
  const h = Math.max(16, height);
  const w = Math.round(h * RATIO);
  return (
    <Image
      src={h > 48 ? "/brand/cls-mark-512.png" : "/brand/cls-mark-128.png"}
      alt=""
      aria-hidden="true"
      width={w}
      height={h}
      priority={priority}
      unoptimized
      draggable={false}
      className={cn("shrink-0 select-none", className)}
    />
  );
}
