"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

export type MeterTone = "ok" | "warn" | "danger" | "neutral" | "brand";

const TONE_VAR: Record<MeterTone, string> = {
  ok: "var(--cls-ok)",
  warn: "var(--cls-warn)",
  danger: "var(--cls-danger)",
  neutral: "var(--cls-fg-3)",
  brand: "var(--cls-brand-500)",
};

/**
 * Segment meter (AD §4): a discrete count out of a small real total (≤ 12), drawn as
 * 30° cells. Always pair it with visible text; `label` is the screen-reader equivalent.
 * Cells fill on mount and only the changed cells transition on later updates.
 */
export function SegmentMeter({
  value,
  total,
  tone = "brand",
  label,
  className,
}: {
  value: number;
  total: number;
  tone?: MeterTone;
  label: string;
  className?: string;
}) {
  const [armed, setArmed] = React.useState(false);
  React.useEffect(() => {
    const id = requestAnimationFrame(() => setArmed(true));
    return () => cancelAnimationFrame(id);
  }, []);

  const cells = Math.max(0, Math.min(total, 12));
  const filled = Math.max(0, Math.min(value, cells));

  return (
    <span
      role="meter"
      aria-label={label}
      aria-valuemin={0}
      aria-valuemax={cells}
      aria-valuenow={filled}
      aria-valuetext={`${filled} of ${cells}`}
      className={cn("inline-flex shrink-0 items-center gap-[3px] px-[2px]", className)}
      style={{ "--cls-seg-on": TONE_VAR[tone] } as React.CSSProperties}
    >
      {Array.from({ length: cells }, (_, i) => (
        <span
          key={i}
          aria-hidden="true"
          data-on={armed && i < filled}
          className="cls-seg h-2 w-2"
          style={{ "--i": i } as React.CSSProperties}
        />
      ))}
    </span>
  );
}
