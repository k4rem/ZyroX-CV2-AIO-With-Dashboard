"use client";

import * as React from "react";
import type { CoreItem } from "@/lib/overviewModel";
import { cutSlantDeg, ringSegments, tickPath } from "@/lib/instruments";
import { deriveHealth } from "@/lib/shellHealth";
import { StatusDot, type Status } from "@/components/ui/status";
import { useHealthReading } from "@/components/shell/health-reading";
import { cn } from "@/lib/utils";

const SIZE = 260;
const C = SIZE / 2;
const OUTER = { r: 116, width: 9, gapDeg: 5 };
const INNER = { r: 100, width: 5, gapDeg: 6 };

/** Inner ring is secondary: same semantics, less ink. */
const FILL: Record<"modules" | "permissions", Record<CoreItem["state"], string>> = {
  modules: { ok: "fill-ok/85", failed: "fill-danger", missing: "fill-warn" },
  permissions: { ok: "fill-ok/50", failed: "fill-danger", missing: "fill-warn" },
};

const STATE_TEXT: Record<"modules" | "permissions", Record<CoreItem["state"], string>> = {
  modules: { ok: "loaded", failed: "failed", missing: "missing" },
  permissions: { ok: "permissions available", failed: "failed", missing: "permissions missing" },
};

const MINOR_TICKS = Array.from({ length: 72 }, (_, i) => i * 5).filter((a) => a % 90 !== 0);
const MAJOR_TICKS = [90, 180, 270];

function Band({
  items,
  band,
  ring,
  active,
  onActive,
  offset,
}: {
  items: CoreItem[] | null;
  band: { r: number; width: number; gapDeg: number };
  ring: "modules" | "permissions";
  active: string | null;
  onActive: (key: string | null) => void;
  offset: number;
}) {
  const opts = { cx: C, cy: C, r: band.r, width: band.width, gapDeg: band.gapDeg, slantDeg: cutSlantDeg(band.width, band.r) };
  if (!items || items.length === 0) {
    // Not reported: a neutral dashed track, never a healthy-looking ring.
    return (
      <circle
        cx={C}
        cy={C}
        r={band.r - band.width / 2}
        fill="none"
        strokeWidth={band.width}
        strokeDasharray="2 5"
        className="stroke-neutral/40"
      />
    );
  }
  const segs = ringSegments(items.length, opts);
  return (
    <g>
      {segs.map((s) => {
        const item = items[s.index];
        return (
          <path
            key={item.key}
            d={s.d}
            data-active-item={active === item.key ? "" : undefined}
            className={cn("cls-arc cursor-default", FILL[ring][item.state])}
            style={{ "--i": offset + s.index } as React.CSSProperties}
            onMouseEnter={() => onActive(item.key)}
            onMouseLeave={() => onActive(null)}
          >
            <title>{`${item.label} — ${STATE_TEXT[ring][item.state]}`}</title>
          </path>
        );
      })}
    </g>
  );
}

function Legend({
  title,
  items,
  ring,
  active,
  onActive,
}: {
  title: string;
  items: CoreItem[] | null;
  ring: "modules" | "permissions";
  active: string | null;
  onActive: (key: string | null) => void;
}) {
  const ok = items?.filter((i) => i.state === "ok").length ?? 0;
  return (
    <div className="min-w-0">
      <div className="flex items-baseline justify-between gap-3 border-b border-line-subtle pb-1.5">
        <h4 className="cls-overline">{title}</h4>
        <span className="font-mono text-small tabular-nums text-fg-1" dir="ltr">
          {items ? `${ok}/${items.length}` : "—"}
        </span>
      </div>
      {items ? (
        <ul className="mt-2 flex flex-wrap gap-x-1 gap-y-1">
          {items.map((item) => (
            <li
              key={item.key}
              tabIndex={0}
              onMouseEnter={() => onActive(item.key)}
              onMouseLeave={() => onActive(null)}
              onFocus={() => onActive(item.key)}
              onBlur={() => onActive(null)}
              className={cn(
                "flex min-w-0 items-center gap-1.5 rounded-xs px-1.5 py-[3px] text-small transition-colors duration-micro",
                active === item.key ? "bg-surface-2 text-fg-1" : "text-fg-2",
              )}
            >
              <span
                aria-hidden="true"
                className={cn(
                  "h-2 w-1.5 shrink-0 -skew-x-[30deg] rtl:skew-x-[30deg]",
                  item.state === "ok" ? (ring === "modules" ? "bg-ok/85" : "bg-ok/50") : item.state === "failed" ? "bg-danger" : "bg-warn",
                )}
              />
              <span className="truncate">{item.label}</span>
              {item.state === "ok" ? (
                <span className="sr-only">{STATE_TEXT[ring].ok}</span>
              ) : (
                <span className={cn("text-caption", item.state === "failed" ? "text-danger" : "text-warn")}>
                  {item.state === "failed" ? "Failed" : "Missing"}
                </span>
              )}
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-1.5 text-small text-fg-3">Not reported by the bot.</p>
      )}
    </div>
  );
}

function botStatus(level: ReturnType<typeof deriveHealth>["level"], online: boolean): { status: Status; label: string } {
  if (level === "offline") return { status: "offline", label: "Offline" };
  if (level === "degraded") return { status: "degraded", label: "Degraded" };
  if (level === "online" || online) return { status: "online", label: "Online" };
  return { status: "unknown", label: "Unknown" };
}

/**
 * System Core (Task A.1): the Overview's focal instrument. Outer ring = required
 * modules, inner ring = this server's module permission requirements; one real
 * item per segment, semantic colour per state. The centre is the live bot reading.
 */
export function SystemCore({
  modules,
  permissions,
  initialLevel,
  initialOnline,
  initialLatencyMs,
}: {
  modules: CoreItem[] | null;
  permissions: CoreItem[] | null;
  initialLevel: ReturnType<typeof deriveHealth>["level"];
  initialOnline: boolean;
  initialLatencyMs: number | null;
}) {
  const [active, setActive] = React.useState<string | null>(null);
  const { reading } = useHealthReading();

  const live = reading.at
    ? deriveHealth({
        status: reading.statusLatency === null ? null : { latency: reading.statusLatency },
        statusFailed: reading.statusFailed,
        health: reading.health,
      })
    : null;
  const level = live?.level ?? initialLevel;
  const latency = live ? live.latencyMs : initialLatencyMs;
  const bot = botStatus(level, live ? level === "online" : initialOnline);

  const modOk = modules?.filter((m) => m.state === "ok").length ?? 0;
  const permOk = permissions?.filter((m) => m.state === "ok").length ?? 0;
  const summary = [
    `Bot ${bot.label.toLowerCase()}${latency != null ? `, ${latency} milliseconds` : ""}`,
    modules ? `${modOk} of ${modules.length} required modules loaded` : "required modules not reported",
    permissions ? `${permOk} of ${permissions.length} modules have the permissions they need` : "permissions not reported",
  ].join(". ");

  const activeItem = [...(modules ?? []), ...(permissions ?? [])].find((i) => i.key === active);

  return (
    <div className="flex h-full flex-col gap-6 p-5 sm:flex-row sm:items-center sm:gap-8 xl:p-6">
      <figure className="relative mx-auto aspect-square w-full max-w-[14rem] shrink-0 sm:mx-0 sm:max-w-none sm:w-[15rem] xl:w-[16.5rem] 4xl:w-[18rem]" aria-label={summary}>
        <svg
          viewBox={`0 0 ${SIZE} ${SIZE}`}
          className="size-full overflow-visible"
          aria-hidden="true"
          data-active={active ? "" : undefined}
        >
          <path d={tickPath(C, C, 125, 128, MINOR_TICKS)} className="stroke-fg-4/60" strokeWidth={1} />
          <path d={tickPath(C, C, 122, 128, MAJOR_TICKS)} className="stroke-fg-3" strokeWidth={1} />
          <path d={tickPath(C, C, 119, 129, [0])} className="stroke-brand-500" strokeWidth={2} />
          <Band items={modules} band={OUTER} ring="modules" active={active} onActive={setActive} offset={0} />
          <Band items={permissions} band={INNER} ring="permissions" active={active} onActive={setActive} offset={modules?.length ?? 0} />
          <circle cx={C} cy={C} r={80} fill="none" className="stroke-line-subtle" strokeWidth={1} />
        </svg>

        <figcaption className="pointer-events-none absolute inset-0 flex flex-col items-center justify-center text-center">
          <span className="flex items-center gap-1.5 text-small text-fg-2">
            <StatusDot status={bot.status} />
            <span key={bot.label} className="cls-num">
              {bot.label}
            </span>
          </span>
          <span className="mt-1 flex items-baseline gap-1 font-mono tabular-nums text-fg-1" dir="ltr">
            <span key={latency ?? "none"} className="cls-num text-[2rem] font-medium leading-none tracking-[-0.02em]">
              {latency ?? "—"}
            </span>
            <span className="text-small text-fg-3">ms</span>
          </span>
          <span className="mt-1.5 text-caption text-fg-3">Gateway latency</span>
        </figcaption>
      </figure>

      <div className="min-w-0 flex-1 space-y-5">
        <div className="flex items-baseline justify-between gap-3">
          <h3 className="text-panel-title text-fg-1">System core</h3>
          <span className="truncate text-caption text-fg-3" aria-live="polite">
            {activeItem ? `${activeItem.label} — ${STATE_TEXT[activeItem.key.startsWith("m-") ? "modules" : "permissions"][activeItem.state]}` : "Outer ring modules · inner ring permissions"}
          </span>
        </div>
        <Legend title="Required modules" items={modules} ring="modules" active={active} onActive={setActive} />
        <Legend title="Permissions" items={permissions} ring="permissions" active={active} onActive={setActive} />
      </div>
    </div>
  );
}
