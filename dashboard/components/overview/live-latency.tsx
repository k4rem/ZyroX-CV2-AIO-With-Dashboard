"use client";

import { useHealthReading } from "@/components/shell/health-reading";

/** Bot latency from the shell's live health poll; the server-rendered reading until the first poll lands. */
export function LiveLatency({ initialMs }: { initialMs: number | null }) {
  const { reading } = useHealthReading();
  const raw = reading.at ? reading.statusLatency : initialMs;
  if (raw == null || !Number.isFinite(raw)) return null;
  const ms = Math.round(raw);
  return (
    <span key={ms} className="cls-num font-mono text-small font-normal tabular-nums text-fg-3" dir="ltr">
      {ms} ms
    </span>
  );
}
