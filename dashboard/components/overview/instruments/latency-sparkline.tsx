"use client";

import * as React from "react";
import { LATENCY_CAPACITY, latencyStats, polylinePath, sparklinePoints } from "@/lib/instruments";
import { DEGRADED_LATENCY_MS } from "@/lib/shellHealth";
import { HEALTH_POLL_MS, useHealthReading } from "@/components/shell/health-reading";
import { cn } from "@/lib/utils";

const HEIGHT = 76;
const PAD_X = 6;

const timeFmt = (at: number) =>
  new Date(at).toLocaleTimeString(undefined, { hour: "2-digit", minute: "2-digit", second: "2-digit", hour12: false });

function useWidth<T extends HTMLElement>(): [React.RefObject<T>, number] {
  const ref = React.useRef<T>(null);
  const [width, setWidth] = React.useState(0);
  React.useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const ro = new ResizeObserver(([entry]) => setWidth(Math.floor(entry.contentRect.width)));
    ro.observe(el);
    return () => ro.disconnect();
  }, []);
  return [ref, width];
}

/**
 * Live latency (Task A.1): gateway latency sampled by the shell's existing 30 s
 * health poll during this browser session. In memory only, last 20 samples;
 * a reload starts a new series. Not history.
 */
export function LatencySparkline({ initialLatencyMs }: { initialLatencyMs: number | null }) {
  const { latencySamples } = useHealthReading();
  const [boxRef, width] = useWidth<HTMLDivElement>();
  const [hover, setHover] = React.useState<number | null>(null);

  const stats = latencyStats(latencySamples);
  const current = stats.latest ?? initialLatencyMs;
  const plotW = Math.max(0, width - PAD_X * 2);
  const points = sparklinePoints(latencySamples, { width: plotW, height: HEIGHT, capacity: LATENCY_CAPACITY, padY: 10 }).map(
    (p) => ({ ...p, x: p.x + PAD_X }),
  );
  const last = points[points.length - 1];
  const prev = points[points.length - 2];
  const shown = hover != null ? points[hover] : null;

  const pick = (clientX: number, rect: DOMRect) => {
    if (points.length === 0) return;
    const x = clientX - rect.left;
    let best = 0;
    for (let i = 1; i < points.length; i++) if (Math.abs(points[i].x - x) < Math.abs(points[best].x - x)) best = i;
    setHover(best);
  };

  const onKey = (e: React.KeyboardEvent) => {
    if (points.length === 0) return;
    if (e.key === "ArrowLeft" || e.key === "ArrowRight") {
      e.preventDefault();
      const d = e.key === "ArrowRight" ? 1 : -1;
      setHover((h) => Math.min(points.length - 1, Math.max(0, (h ?? points.length - 1) + d)));
    } else if (e.key === "Escape") setHover(null);
  };

  const summary =
    stats.count === 0
      ? "No latency samples yet in this session."
      : `${stats.count} latency samples this session, latest ${stats.latest} ms, range ${stats.min} to ${stats.max} ms.`;

  return (
    <div className="flex h-full flex-col gap-3 p-5">
      <div className="flex flex-wrap items-baseline gap-x-4 gap-y-1">
        <h3 className="text-panel-title text-fg-1">Live latency</h3>
        <span className="text-caption text-fg-3">
          This session · {stats.count === 1 ? "1 sample" : `${stats.count} samples`} · every {HEALTH_POLL_MS / 1000} s
        </span>
        <span className="ms-auto flex items-baseline gap-3 font-mono tabular-nums" dir="ltr">
          {stats.count > 1 && stats.min !== stats.max && (
            <span className="text-caption text-fg-3">
              {stats.min}–{stats.max} ms
            </span>
          )}
          <span className="flex items-baseline gap-1 text-fg-1">
            <span key={shown ? `h${hover}` : current ?? "none"} className="cls-num text-kpi-sm">
              {shown ? shown.ms : current ?? "—"}
            </span>
            <span className="text-small text-fg-3">ms</span>
          </span>
        </span>
      </div>

      <div
        ref={boxRef}
        dir="ltr"
        tabIndex={points.length > 0 ? 0 : -1}
        role="img"
        aria-label={summary}
        aria-describedby={shown ? "ov-latency-point" : undefined}
        onKeyDown={onKey}
        onBlur={() => setHover(null)}
        onMouseMove={(e) => pick(e.clientX, e.currentTarget.getBoundingClientRect())}
        onMouseLeave={() => setHover(null)}
        className="relative min-h-[76px] flex-1 rounded-xs"
      >
        {width > 0 && (
          <svg width={width} height={HEIGHT} className="absolute inset-x-0 top-0 block" aria-hidden="true">
            <line x1={PAD_X} x2={width - PAD_X} y1={HEIGHT - 0.5} y2={HEIGHT - 0.5} className="stroke-line-subtle" />
            {points.length > 1 && (
              <path
                d={polylinePath(points.slice(0, -1))}
                fill="none"
                className="stroke-brand-400"
                strokeWidth={1.5}
                strokeLinejoin="round"
                strokeLinecap="round"
              />
            )}
            {prev && last && (
              <path
                key={`seg-${last.at}`}
                d={polylinePath([prev, last])}
                pathLength={1}
                fill="none"
                className="cls-draw stroke-brand-400"
                strokeWidth={1.5}
                strokeLinecap="round"
              />
            )}
            {points.map((p, i) => (
              <circle
                key={p.at}
                cx={p.x}
                cy={p.y}
                r={i === points.length - 1 ? 3 : 1.75}
                className={cn(
                  p.ms > DEGRADED_LATENCY_MS ? "fill-warn" : i === points.length - 1 ? "fill-brand-300" : "fill-fg-3",
                )}
              />
            ))}
            {shown && (
              <line x1={shown.x} x2={shown.x} y1={0} y2={HEIGHT} className="stroke-fg-4" strokeDasharray="2 3" />
            )}
          </svg>
        )}
        {stats.count < 2 && (
          <p className="absolute inset-x-0 bottom-2 px-2 text-center text-caption text-fg-3">
            The line builds as samples arrive. Reloading starts a new series.
          </p>
        )}
        {shown && (
          <span
            id="ov-latency-point"
            className="pointer-events-none absolute top-1 rounded-xs border border-line-strong bg-surface-2 px-1.5 py-0.5 font-mono text-caption tabular-nums text-fg-1"
            style={{ left: Math.min(Math.max(shown.x - 48, 0), Math.max(0, width - 104)) }}
          >
            {shown.ms} ms · {timeFmt(shown.at)}
          </span>
        )}
      </div>
    </div>
  );
}
