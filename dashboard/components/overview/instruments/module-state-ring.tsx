"use client";

import * as React from "react";
import { COVERAGE_LABELS, COVERAGE_ORDER, type CoverageBucket } from "@/lib/overviewModel";
import { cutSlantDeg, ringSegments } from "@/lib/instruments";
import { cn } from "@/lib/utils";

const SIZE = 132;
const C = SIZE / 2;
const BAND = { r: 60, width: 9 };

const FILL: Record<CoverageBucket, string> = {
  on: "fill-ok",
  partial: "fill-warn",
  off: "fill-fg-4/50",
  unavailable: "fill-neutral/50",
};
const SWATCH: Record<CoverageBucket, string> = {
  on: "bg-ok",
  partial: "bg-warn",
  off: "bg-fg-4/50",
  unavailable: "bg-neutral/50",
};

/**
 * Module state (Task A.1): one segment per module in the matrix, ordered by state.
 * A distribution of real counts — never a score. Subordinate to the System Core:
 * single thin ring, no ticks.
 */
export function ModuleStateRing({ modules }: { modules: { key: string; name: string; bucket: CoverageBucket }[] }) {
  const [active, setActive] = React.useState<CoverageBucket | null>(null);
  const ordered = [...modules].sort((a, b) => COVERAGE_ORDER.indexOf(a.bucket) - COVERAGE_ORDER.indexOf(b.bucket));
  const counts = Object.fromEntries(COVERAGE_ORDER.map((b) => [b, modules.filter((m) => m.bucket === b).length])) as Record<
    CoverageBucket,
    number
  >;
  const shown = COVERAGE_ORDER.filter((b) => b !== "unavailable" || counts.unavailable > 0);
  const segs = ringSegments(ordered.length, {
    cx: C,
    cy: C,
    r: BAND.r,
    width: BAND.width,
    gapDeg: 4,
    slantDeg: cutSlantDeg(BAND.width, BAND.r),
  });
  const summary = shown.map((b) => `${COVERAGE_LABELS[b]} ${counts[b]}`).join(", ");

  return (
    <div className="flex h-full flex-col gap-4 p-5">
      <h3 className="text-panel-title text-fg-1">Module state</h3>
      <div className="flex items-center gap-5">
        <figure className="relative size-[7.5rem] shrink-0" aria-label={`Module state: ${summary}`}>
          <svg viewBox={`0 0 ${SIZE} ${SIZE}`} className="size-full" aria-hidden="true" data-active={active ? "" : undefined}>
            {segs.map((s) => {
              const m = ordered[s.index];
              return (
                <path
                  key={s.index}
                  d={s.d}
                  data-active-item={active === m.bucket ? "" : undefined}
                  className={cn("cls-arc", FILL[m.bucket])}
                  style={{ "--i": s.index } as React.CSSProperties}
                  onMouseEnter={() => setActive(m.bucket)}
                  onMouseLeave={() => setActive(null)}
                >
                  <title>{`${m.name} — ${COVERAGE_LABELS[m.bucket]}`}</title>
                </path>
              );
            })}
          </svg>
          <figcaption className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center">
            <span className="font-mono text-kpi-sm tabular-nums text-fg-1" dir="ltr">
              {counts.on}
              <span className="text-small text-fg-3">/{modules.length}</span>
            </span>
            <span className="text-caption text-fg-3">on</span>
          </figcaption>
        </figure>
        <ul className="min-w-0 flex-1 space-y-0.5">
          {shown.map((b) => (
            <li
              key={b}
              tabIndex={0}
              onMouseEnter={() => setActive(b)}
              onMouseLeave={() => setActive(null)}
              onFocus={() => setActive(b)}
              onBlur={() => setActive(null)}
              className={cn(
                "-mx-1 flex items-center gap-2 rounded-xs px-1 py-1 text-small transition-colors duration-micro",
                active === b ? "bg-surface-2 text-fg-1" : "text-fg-2",
              )}
            >
              <span aria-hidden="true" className={cn("h-2 w-1.5 shrink-0 -skew-x-[30deg] rtl:skew-x-[30deg]", SWATCH[b])} />
              <span>{COVERAGE_LABELS[b]}</span>
              <span className="ms-auto font-mono tabular-nums text-fg-1">{counts[b]}</span>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}
