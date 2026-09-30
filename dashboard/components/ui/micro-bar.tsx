import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Mini bars (AD §4): a few real counts compared against each other. Neutral ink —
 * composition is a fact, not a status. Each row carries its number as text.
 */
export function MicroBars({
  rows,
  label,
  className,
}: {
  rows: { key: string; label: string; value: number }[];
  label: string;
  className?: string;
}) {
  const max = Math.max(1, ...rows.map((r) => r.value));
  return (
    <dl aria-label={label} className={cn("space-y-1.5", className)}>
      {rows.map((r) => (
        <div key={r.key} className="grid grid-cols-[6.5rem_minmax(0,1fr)_2.5rem] items-center gap-3 text-small">
          <dt className="truncate text-fg-2">{r.label}</dt>
          <span aria-hidden="true" className="h-1 bg-surface-3">
            <span className="cls-fill block h-full bg-fg-4" style={{ transform: `scaleX(${r.value / max})` }} />
          </span>
          <dd className="text-end font-mono tabular-nums text-fg-1">{r.value.toLocaleString()}</dd>
        </div>
      ))}
    </dl>
  );
}
