"use client";

import * as React from "react";
import { LifeBuoy, MessageSquare, ScrollText, ShieldAlert, UserRound, Workflow, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { ClsMark } from "@/components/brand/cls-mark";
import {
  hexEdgeMidpoint,
  hexEdgeOutwardNormal,
  hexEdgeSegment,
  hexEdgeTick,
  hexVertices,
} from "@/lib/hexGeometry";
import { PERIMETER_DOMAINS, type PerimeterDomain } from "@/lib/landingDomains";

export { PERIMETER_DOMAINS, type PerimeterDomain };

export interface PerimeterMarkProps {
  variant?: "hero" | "auth" | "static";
  locked?: boolean;
  activeDomain?: PerimeterDomain | null;
  className?: string;
  showLabels?: boolean;
  parallax?: boolean;
  onDomainSelect?: (domain: PerimeterDomain) => void;
}

const DOMAIN_ICONS: Record<PerimeterDomain, LucideIcon> = {
  Security: ShieldAlert,
  Tickets: LifeBuoy,
  Logging: ScrollText,
  Messaging: MessageSquare,
  Roles: UserRound,
  Automation: Workflow,
};

const CX = 100;
const CY = 100;
const OUTER_R = 88;
const MID_R = 68;
const INNER_R = 44;
const VIEW = 200;
const LABEL_OFFSET = 11;

function OuterRing({
  radius,
  gap,
  activeIndex,
  className,
  style,
}: {
  radius: number;
  gap: number;
  activeIndex: number;
  className?: string;
  style?: React.CSSProperties;
}) {
  const verts = hexVertices(CX, CY, radius);
  return (
    <g className={className} style={style}>
      {verts.map((_, i) => (
        <path
          key={i}
          d={hexEdgeSegment(verts, i, gap)}
          fill="none"
          stroke="currentColor"
          strokeWidth={1.5}
          strokeLinecap="butt"
          className={cn(
            "cls-perimeter-seg cls-perimeter-outer-seg transition-[stroke,opacity] duration-standard",
            i === activeIndex ? "text-brand-400 opacity-100" : "text-fg-3 opacity-40",
          )}
          data-seg={i}
        />
      ))}
    </g>
  );
}

function InnerRing({
  radius,
  gap,
  className,
  style,
}: {
  radius: number;
  gap: number;
  className?: string;
  style?: React.CSSProperties;
}) {
  const verts = hexVertices(CX, CY, radius);
  return (
    <g className={className} style={style}>
      {verts.map((_, i) => (
        <path
          key={i}
          d={hexEdgeSegment(verts, i, gap)}
          fill="none"
          stroke="currentColor"
          strokeWidth={1}
          strokeLinecap="butt"
          className="cls-perimeter-seg cls-perimeter-inner-seg text-fg-3/35"
          data-seg={i}
        />
      ))}
    </g>
  );
}

function ControlTicks({ radius, className, style }: { radius: number; className?: string; style?: React.CSSProperties }) {
  const verts = hexVertices(CX, CY, radius);
  return (
    <g className={cn("text-fg-3/25", className)} style={style}>
      {verts.map((_, i) => (
        <path
          key={i}
          d={hexEdgeTick(verts, i, CX, CY, 4)}
          fill="none"
          stroke="currentColor"
          strokeWidth={1}
          strokeLinecap="butt"
          className="cls-perimeter-mid-tick"
        />
      ))}
      {verts.map((_, i) => {
        const [mx, my] = hexEdgeMidpoint(verts, i);
        const [nx, ny] = hexEdgeOutwardNormal(verts, i, CX, CY);
        const px = mx + nx * 2;
        const py = my + ny * 2;
        return (
          <circle key={`d-${i}`} cx={px} cy={py} r={0.75} fill="currentColor" className="opacity-60" />
        );
      })}
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
  onDomainSelect,
}: PerimeterMarkProps) {
  const [gap, setGap] = React.useState(0.03);
  const [markPx, setMarkPx] = React.useState(72);
  const rootRef = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const el = rootRef.current;
    if (!el || variant !== "hero") return;
    const ro = new ResizeObserver(([entry]) => {
      const h = entry.contentRect.height;
      setMarkPx(Math.round(h * 0.26));
    });
    ro.observe(el);
    return () => ro.disconnect();
  }, [variant]);

  React.useEffect(() => {
    if (!locked) {
      setGap(0.03);
      return;
    }
    const start = performance.now();
    const dur = 480;
    let raf = 0;
    const step = (t: number) => {
      const p = Math.min(1, (t - start) / dur);
      setGap(0.03 * (1 - p));
      if (p < 1) raf = requestAnimationFrame(step);
    };
    raf = requestAnimationFrame(step);
    return () => cancelAnimationFrame(raf);
  }, [locked]);

  const activeIndex = activeDomain != null ? PERIMETER_DOMAINS.indexOf(activeDomain) : -1;
  const outerVerts = hexVertices(CX, CY, OUTER_R);

  const sizeClass =
    variant === "hero"
      ? "w-full max-w-[min(100%,720px)] aspect-square"
      : variant === "auth"
        ? "h-24 w-24"
        : "h-40 w-40";

  const markHeight = variant === "hero" ? markPx : variant === "auth" ? 28 : 40;

  const labelPositions = PERIMETER_DOMAINS.map((label, i) => {
    const [mx, my] = hexEdgeMidpoint(outerVerts, i);
    const [nx, ny] = hexEdgeOutwardNormal(outerVerts, i, CX, CY);
    const lx = mx + nx * LABEL_OFFSET;
    const ly = my + ny * LABEL_OFFSET;
    const isVerticalSide = Math.abs(nx) < 0.35;
    return { label, lx, ly, nx, ny, isVerticalSide, active: i === activeIndex };
  });

  return (
    <div
      ref={rootRef}
      className={cn("relative mx-auto shrink-0", sizeClass, className)}
      data-perimeter-locked={locked || undefined}
      data-perimeter-variant={variant}
    >
      <div
        className={cn(
          "cls-perimeter-core pointer-events-none absolute left-1/2 top-1/2 h-[46%] w-[46%] -translate-x-1/2 -translate-y-1/2 rounded-full cls-perimeter-core-glow",
          parallax && "cls-depth-bg",
        )}
        aria-hidden="true"
      />

      <div className="absolute inset-[10%]">
        <svg
          viewBox={`0 0 ${VIEW} ${VIEW}`}
          className="h-full w-full overflow-visible"
          aria-hidden="true"
          role="presentation"
        >
          <OuterRing
            radius={OUTER_R}
            gap={gap}
            activeIndex={activeIndex}
            className={cn("cls-perimeter-outer", parallax && "cls-depth-ui")}
          />
          <ControlTicks
            radius={MID_R}
            className={cn("cls-perimeter-middle", parallax && "cls-depth-mid")}
          />
          <InnerRing
            radius={INNER_R}
            gap={gap}
            className={cn(
              "cls-perimeter-inner",
              parallax && "cls-depth-mid",
              locked && "text-brand-500/50",
            )}
          />
        </svg>
      </div>

      {showLabels && variant === "hero" ? (
        <div className="absolute inset-0">
          {labelPositions.map(({ label, lx, ly, active }) => {
            const Icon = DOMAIN_ICONS[label];
            return (
              <button
                key={label}
                type="button"
                aria-pressed={active}
                className={cn(
                  "cls-perimeter-edge-label absolute flex items-center gap-1 rounded-sm border px-1.5 py-1 text-[11px] leading-none outline-none",
                  "focus-visible:ring-2 focus-visible:ring-brand-400",
                  active ? "border-brand-400/50 bg-brand-600/15 text-brand-300" : "border-line bg-void/80 text-fg-3 hover:text-fg-1",
                )}
                style={{
                  left: `${(lx / VIEW) * 100}%`,
                  top: `${(ly / VIEW) * 100}%`,
                  transform: "translate(-50%, -50%)",
                }}
                onClick={() => onDomainSelect?.(label)}
              >
                <Icon className="size-3.5 shrink-0" strokeWidth={1.75} aria-hidden="true" />
                <span className="max-sm:sr-only">{label}</span>
              </button>
            );
          })}
        </div>
      ) : null}

      <div
        className={cn(
          "pointer-events-none absolute inset-0 flex items-center justify-center",
          parallax && "cls-depth-fg",
        )}
      >
        <ClsMark height={markHeight} priority={variant === "hero"} />
      </div>
    </div>
  );
}
