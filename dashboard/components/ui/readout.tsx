"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Readout cell (AD §4): overline label over a compact value. Cells live in a
 * `ReadoutRail` and are separated by hairlines, not boxes.
 */
export function Readout({
  label,
  children,
  className,
}: {
  label: string;
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div className={cn("min-w-0 px-4 py-3", className)}>
      <dt className="cls-overline truncate">{label}</dt>
      <dd className="mt-1.5 flex min-w-0 items-center gap-2 text-readout text-fg-1">{children}</dd>
    </div>
  );
}

/**
 * Marks a factual value that changed since the last read (e.g. after Refresh) with
 * one brief wash. The first render never washes.
 */
export function ChangeMark({
  watch,
  children,
  className,
}: {
  watch: string | number | boolean | null;
  children: React.ReactNode;
  className?: string;
}) {
  const prev = React.useRef(watch);
  const [generation, setGeneration] = React.useState(0);
  React.useEffect(() => {
    if (prev.current !== watch) {
      prev.current = watch;
      setGeneration((g) => g + 1);
    }
  }, [watch]);
  return (
    <span key={generation} className={cn("-mx-1 inline-flex min-w-0 items-center gap-2 rounded-xs px-1", generation > 0 && "cls-changed", className)}>
      {children}
    </span>
  );
}
