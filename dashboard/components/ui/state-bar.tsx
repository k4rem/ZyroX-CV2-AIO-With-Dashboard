"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export interface StatePart {
  key: string;
  label: string;
  value: number;
  /** Tailwind background class for the part, e.g. `bg-ok`. */
  fill: string;
}

/**
 * State distribution bar (AD §4): how a real set of items splits across states.
 * Renders a legend with counts, so the bar is never the only carrier of meaning.
 * Zero-count parts are kept in the legend and dropped from the bar.
 */
export function StateBar({ parts, label, className }: { parts: StatePart[]; label: string; className?: string }) {
  const [armed, setArmed] = React.useState(false);
  React.useEffect(() => {
    const id = requestAnimationFrame(() => setArmed(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const total = parts.reduce((n, p) => n + p.value, 0);
  const summary = parts.map((p) => `${p.label} ${p.value}`).join(", ");

  return (
    <div className={className}>
      <div role="img" aria-label={`${label}: ${summary}`} className="h-1.5 bg-surface-3">
        <div className="cls-fill flex h-full gap-[2px]" style={{ transform: armed ? "none" : "scaleX(0)" }}>
          {total > 0 &&
            parts
              .filter((p) => p.value > 0)
              .map((p) => (
                <span
                  key={p.key}
                  aria-hidden="true"
                  className={cn("h-full", p.fill)}
                  style={{ flexGrow: p.value, flexBasis: 0 }}
                />
              ))}
        </div>
      </div>
      <ul className="mt-2.5 grid grid-cols-2 gap-x-4 gap-y-1.5">
        {parts.map((p) => (
          <li key={p.key} className="flex items-center gap-2 text-small">
            <span aria-hidden="true" className={cn("size-1.5 shrink-0", p.fill)} />
            <span className="text-fg-2">{p.label}</span>
            <span className="ms-auto font-mono tabular-nums text-fg-1">{p.value}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
