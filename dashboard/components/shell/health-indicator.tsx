"use client";

import * as React from "react";
import { usePathname } from "next/navigation";
import { parseDashboardPath } from "@/lib/shellNav";
import {
  deriveHealth,
  permissionSummaryForGuild,
  type HealthLevel,
} from "@/lib/shellHealth";
import { cn } from "@/lib/utils";
import { useHealthReading } from "./health-reading";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { StatusLabel, type Status } from "@/components/ui/status";

const LEVEL_STATUS: Record<HealthLevel, Status> = {
  loading: "unknown",
  online: "online",
  degraded: "degraded",
  offline: "offline",
};

const LEVEL_TEXT: Record<HealthLevel, string> = {
  loading: "Checking",
  online: "Bot online",
  degraded: "Degraded",
  offline: "Bot unreachable",
};

function Row({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex min-h-7 items-center justify-between gap-3 py-0.5">
      <dt className="text-small text-fg-3">{label}</dt>
      <dd className="min-w-0 text-end text-small text-fg-1">{children}</dd>
    </div>
  );
}

const timeFmt = new Intl.DateTimeFormat(undefined, {
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hour12: false,
});

/**
 * Global bot health (DS §15.3). Every value comes from `/bot/status` and
 * `/system/health`; nothing is assumed. While loading or when a probe fails the
 * indicator says so instead of claiming health.
 */
export function HealthIndicator() {
  const pathname = usePathname() ?? "";
  const { guildId } = parseDashboardPath(pathname);
  const { reading } = useHealthReading();

  const snapshot = deriveHealth({
    status: reading.statusLatency === null ? null : { latency: reading.statusLatency },
    statusFailed: reading.statusFailed,
    health: reading.health,
  });
  // An ended session is reported as such instead of "Bot unreachable" (the bot may be fine).
  const status: Status = reading.sessionEnded ? "warning" : LEVEL_STATUS[snapshot.level];
  const text = reading.sessionEnded ? "Session ended" : LEVEL_TEXT[snapshot.level];

  // Announce state transitions (not every poll) to assistive tech.
  const lastAnnounced = React.useRef<string | null>(null);
  const [announcement, setAnnouncement] = React.useState("");
  React.useEffect(() => {
    if (snapshot.level === "loading" && !reading.sessionEnded) return;
    if (lastAnnounced.current === text) return;
    if (lastAnnounced.current !== null) setAnnouncement(`System status: ${text}`);
    lastAnnounced.current = text;
  }, [text, snapshot.level, reading.sessionEnded]);

  const perms = permissionSummaryForGuild(reading.health, guildId);
  const modules = reading.health?.modules;
  const scheduler = reading.health?.scheduler;
  const postgres = reading.health?.postgres;

  return (
    <Popover>
      <span role="status" aria-live="polite" className="sr-only">
        {announcement}
      </span>
      <PopoverTrigger asChild>
        <button
          type="button"
          aria-label={`System status: ${text}${snapshot.latencyMs !== null ? `, ${snapshot.latencyMs} milliseconds` : ""}`}
          className={cn(
            "flex h-10 items-center gap-2 rounded-sm px-2 text-small md:h-7 outline-none transition-colors duration-micro",
            "hover:bg-surface-3 data-[state=open]:bg-surface-3",
            "focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-400",
          )}
        >
          <StatusLabel status={status} live={snapshot.level === "online" && !reading.sessionEnded}>
            <span className="truncate">{text}</span>
          </StatusLabel>
          {snapshot.latencyMs !== null ? (
            <span className="cls-mono-data hidden text-fg-3 md:inline" dir="ltr">{snapshot.latencyMs} ms</span>
          ) : null}
        </button>
      </PopoverTrigger>

      <PopoverContent align="end" className="w-[300px]">
        <div className="border-b border-line px-3 py-2">
          <p className="cls-overline">System health</p>
        </div>
        <dl className="px-3 py-2">
          <Row label="Bot">
            <StatusLabel status={status}>{text}</StatusLabel>
          </Row>
          <Row label="Gateway latency">
            {snapshot.latencyMs !== null ? <span className="cls-mono-data" dir="ltr">{snapshot.latencyMs} ms</span> : "Unknown"}
          </Row>
          <Row label="Required modules">
            {!modules ? (
              "Unknown"
            ) : (modules.required_failed ?? []).length > 0 ? (
              <StatusLabel status="critical">{(modules.required_failed ?? []).length} failed</StatusLabel>
            ) : (modules.required_ok ?? []).length > 0 ? (
              <StatusLabel status="healthy">{(modules.required_ok ?? []).length} loaded</StatusLabel>
            ) : (
              <span className="text-fg-3">None reported</span>
            )}
          </Row>
          <Row label="Database">
            {!postgres ? (
              "Unknown"
            ) : !postgres.enabled ? (
              <StatusLabel status="disabled">Not enabled</StatusLabel>
            ) : postgres.connected ? (
              <StatusLabel status="healthy">Connected</StatusLabel>
            ) : (
              <StatusLabel status="critical">Disconnected</StatusLabel>
            )}
          </Row>
          <Row label="Scheduler">
            {!scheduler ? (
              "Unknown"
            ) : scheduler.worker_running ? (
              <StatusLabel status="healthy">Running</StatusLabel>
            ) : (
              <StatusLabel status="disabled">Idle</StatusLabel>
            )}
          </Row>
          {guildId ? (
            <Row label="This server">
              {!perms.known ? (
                "Unknown"
              ) : perms.missingModules.length === 0 ? (
                <StatusLabel status="healthy">Permissions OK</StatusLabel>
              ) : (
                <StatusLabel status="warning">
                  {perms.missingModules.length} module{perms.missingModules.length === 1 ? "" : "s"} missing permissions
                </StatusLabel>
              )}
            </Row>
          ) : null}
        </dl>

        {snapshot.reasons.length > 0 ? (
          <ul className="border-t border-line px-3 py-2">
            {snapshot.reasons.map((r) => (
              <li key={r} className="py-0.5">
                <StatusLabel status={status} className="items-start [&>span:first-child]:mt-1.5">
                  {r}
                </StatusLabel>
              </li>
            ))}
          </ul>
        ) : null}

        {reading.sessionEnded ? (
          <p className="border-t border-line px-3 py-2 text-small text-fg-2">
            Your dashboard session is no longer valid.{" "}
            <a
              href="/?notice=session-ended"
              className="rounded-xs text-brand-400 underline-offset-2 hover:underline focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-400"
            >
              Sign in again
            </a>
          </p>
        ) : null}

        {reading.healthFailed && !reading.statusFailed && !reading.sessionEnded ? (
          <p className="border-t border-line px-3 py-2 text-small text-fg-3">
            Detailed system health could not be read.
          </p>
        ) : null}

        <div className="border-t border-line px-3 py-1.5 text-small text-fg-3">
          {reading.at ? `Checked ${timeFmt.format(reading.at)}` : "Checking…"}
        </div>
      </PopoverContent>
    </Popover>
  );
}
