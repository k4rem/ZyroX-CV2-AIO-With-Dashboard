"use client";

import * as React from "react";
import { cn } from "@/lib/utils";
import { ClsMark } from "@/components/brand/cls-mark";
import { hexEdgeSegment, hexLabelAnchor, hexVertices } from "@/lib/hexGeometry";
import { usePerimeterParallax } from "@/components/landing/use-parallax";

export const PERIMETER_DOMAINS = [
  "Security",
  "Support",
  "Recovery",
  "Automation",
  "Moderation",
  "Audit",
] as const;

export type PerimeterDomain = (typeof PERIMETER_DOMAINS)[number];

export interface PerimeterMarkProps {
  /** hero ≈560px, auth ≈96px visual scale */
  variant?: "hero" | "auth" | "static";
  locked?: boolean;
  /** Highlight one outer segment (hover sync with domain list). */
  activeDomain?: PerimeterDomain | null;
  className?: string;
  showLabels?: boolean;
  /** Enable pointer parallax (hero only, fine pointer). */
  parallax?: boolean;
}

const CX = 100;
const CY = 100;
const OUTER_R = 88;
const MID_R = 65;
const INNER_R = 44;

function Ring({
  radius,
  strokeWidth,
  className,
  segmentClass,
  style,
}: {
  radius: number;
  strokeWidth: number;
  className?: string;
  segmentClass?: string;
  style?: React.CSSProperties;
}) {
  const verts = hexVertices(CX, CY, radius);
  return (
    <g className={className} style={style}>
      {verts.map((_, i) => (
        <path
          key={i}
          d={hexEdgeSegment(verts, i, 0.03)}
          fill="none"
          stroke="currentColor"
          strokeWidth={strokeWidth}
          strokeLinecap="butt"
          className={segmentClass}
          data-seg={i}
        />
      ))}
    </g>
  );
}

export function PerimeterMark({
  variant = "hero",
  locked = false,
  activeDomain = null,
  className,
  showLabels = true,
  parallax = false,
}: PerimeterMarkProps) {
  const sizeClass =
    variant === "hero" ? "h-[min(560px,88vw)] w-[min(560px,88vw)]" : variant === "auth" ? "h-24 w-24" : "h-40 w-40";
  const markHeight = variant === "hero" ? 72 : variant === "auth" ? 28 : 40;

  const [parallaxOn, setParallaxOn] = React.useState(false);
  React.useEffect(() => {
    const ok =
      parallax &&
      variant === "hero" &&
      !window.matchMedia("(prefers-reduced-motion: reduce)").matches &&
      !window.matchMedia("(pointer: coarse)").matches;
    setParallaxOn(ok);
  }, [parallax, variant]);
  const { ref, offset } = usePerimeterParallax(parallaxOn);

  const activeIndex =
    activeDomain != null ? PERIMETER_DOMAINS.indexOf(activeDomain) : -1;

  const outerVerts = hexVertices(CX, CY, OUTER_R);

  return (
    <div
      ref={ref}
      className={cn("relative mx-auto shrink-0", sizeClass, className)}
      data-perimeter-locked={locked || undefined}
      data-perimeter-variant={variant}
    >
      <div
        className="pointer-events-none absolute inset-[18%] rounded-full bg-brand-600/[0.08] blur-2xl cls-perimeter-core-glow"
        aria-hidden="true"
      />
      <svg
        viewBox="0 0 200 200"
        className="relative h-full w-full overflow-visible"
        aria-hidden="true"
        role="presentation"
      >
        <g
          className="text-fg-3/40 cls-perimeter-outer transition-transform duration-emphasized ease-cls-in-out"
          style={{ transform: `translate(${offset.ox}px, ${offset.oy}px)` }}
        >
          <Ring
            radius={OUTER_R}
            strokeWidth={1.5}
            segmentClass={cn(
              "cls-perimeter-seg cls-perimeter-outer-seg",
              locked && "cls-perimeter-lock-outer",
            )}
          />
        </g>
        <g
          className="text-fg-3/30 cls-perimeter-middle transition-transform duration-emphasized ease-cls-in-out"
          style={{ transform: `translate(${offset.mx}px, ${offset.my}px)` }}
        >
          <Ring radius={MID_R} strokeWidth={1} segmentClass="cls-perimeter-seg cls-perimeter-mid-seg" />
        </g>
        <g
          className="text-brand-500/60 cls-perimeter-inner transition-transform duration-emphasized ease-cls-in-out"
          style={{ transform: `translate(${offset.ix}px, ${offset.iy}px)` }}
        >
          <Ring
            radius={INNER_R}
            strokeWidth={1.5}
            segmentClass={cn(
              "cls-perimeter-seg cls-perimeter-inner-seg",
              locked && "cls-perimeter-lock-inner",
            )}
          />
        </g>

        {showLabels && variant === "hero" ? (
          <g className="cls-perimeter-labels max-md:hidden">
            {PERIMETER_DOMAINS.map((label, i) => {
              const [lx, ly] = hexLabelAnchor(outerVerts, i, 14);
              const active = i === activeIndex;
              return (
                <text
                  key={label}
                  x={lx}
                  y={ly}
                  textAnchor="middle"
                  dominantBaseline="middle"
                  className={cn(
                    "cls-overline fill-fg-3 text-[9px] cls-perimeter-label",
                    active && "fill-brand-400",
                  )}
                >
                  {label}
                </text>
              );
            })}
          </g>
        ) : null}
      </svg>

      <div className="pointer-events-none absolute inset-0 flex items-center justify-center">
        <ClsMark height={markHeight} priority={variant === "hero"} />
      </div>
    </div>
  );
}
