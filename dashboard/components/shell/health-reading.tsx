"use client";

import * as React from "react";
import { api } from "@/lib/api";
import type { SystemHealthLike } from "@/lib/shellHealth";
import { appendLatencySample, type LatencySample } from "@/lib/instruments";

export const HEALTH_POLL_MS = 30_000;

export interface HealthReading {
  statusLatency: number | null;
  statusFailed: boolean;
  /** A probe came back 401: the dashboard session ended, which is not the same as the bot being down. */
  sessionEnded: boolean;
  health: SystemHealthLike | null;
  healthFailed: boolean;
  at: Date | null;
}

const INITIAL: HealthReading = {
  statusLatency: null,
  statusFailed: false,
  sessionEnded: false,
  health: null,
  healthFailed: false,
  at: null,
};

/** A hung probe must resolve to "unreachable", never freeze the last (possibly green) reading. */
const PROBE_TIMEOUT_MS = 8_000;

function withTimeout<T>(p: Promise<T>): Promise<T> {
  return new Promise<T>((resolve, reject) => {
    const t = setTimeout(() => reject(new Error("timeout")), PROBE_TIMEOUT_MS);
    p.then(
      (v) => {
        clearTimeout(t);
        resolve(v);
      },
      (e) => {
        clearTimeout(t);
        reject(e);
      },
    );
  });
}

class ProbeError extends Error {
  constructor(public status: number) {
    super(String(status));
  }
}

async function readHealth(): Promise<SystemHealthLike | null> {
  const res = await fetch("/api/bot/system/health", {
    credentials: "same-origin",
    cache: "no-store",
    headers: { Accept: "application/json" },
    signal: AbortSignal.timeout(PROBE_TIMEOUT_MS),
  });
  if (!res.ok) throw new ProbeError(res.status);
  return (await res.json()) as SystemHealthLike;
}

function isUnauthorized(result: PromiseSettledResult<unknown>) {
  return result.status === "rejected" && (result.reason as { status?: number } | undefined)?.status === 401;
}

interface HealthReadingContextValue {
  reading: HealthReading;
  /** Session-only, in-memory, bounded (LATENCY_CAPACITY). Cleared on reload. */
  latencySamples: LatencySample[];
  /** Probe now (e.g. "Check again"). Ignored while a probe is in flight. */
  refresh: () => void;
}

const HealthReadingContext = React.createContext<HealthReadingContextValue | null>(null);

/**
 * The one bot-health poll for the dashboard shell (DS §15.3): `/bot/status` +
 * `/system/health` every 30 s while the tab is visible. The topbar indicator and
 * the Overview's live latency both read it, so no page adds its own interval.
 */
export function HealthReadingProvider({ children }: { children: React.ReactNode }) {
  const [reading, setReading] = React.useState<HealthReading>(INITIAL);
  const [latencySamples, setLatencySamples] = React.useState<LatencySample[]>([]);
  const tickRef = React.useRef<() => void>(() => {});

  React.useEffect(() => {
    let cancelled = false;
    let inFlight = false;
    let timer: ReturnType<typeof setTimeout> | undefined;

    const schedule = () => {
      if (cancelled) return;
      if (timer) clearTimeout(timer);
      timer = setTimeout(() => {
        if (document.visibilityState === "visible") void tick();
        else schedule();
      }, HEALTH_POLL_MS);
    };

    const tick = async () => {
      if (inFlight) return;
      inFlight = true;
      if (timer) clearTimeout(timer);
      try {
        const [status, health] = await Promise.allSettled([withTimeout(api.getBotStatus()), readHealth()]);
        if (cancelled) return;
        const at = new Date();
        const latency = status.status === "fulfilled" ? status.value.latency : null;
        setReading({
          statusLatency: latency,
          statusFailed: status.status === "rejected",
          sessionEnded: isUnauthorized(status) || isUnauthorized(health),
          health: health.status === "fulfilled" ? health.value : null,
          healthFailed: health.status === "rejected",
          at,
        });
        if (latency !== null) {
          setLatencySamples((buf) => appendLatencySample(buf, { at: at.getTime(), ms: latency }));
        }
      } finally {
        inFlight = false;
        schedule();
      }
    };

    tickRef.current = () => void tick();

    const onVisible = () => {
      if (document.visibilityState === "visible") void tick();
    };

    void tick();
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      cancelled = true;
      tickRef.current = () => {};
      if (timer) clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisible);
    };
  }, []);

  const refresh = React.useCallback(() => tickRef.current(), []);
  const value = React.useMemo(() => ({ reading, latencySamples, refresh }), [reading, latencySamples, refresh]);

  return <HealthReadingContext.Provider value={value}>{children}</HealthReadingContext.Provider>;
}

export function useHealthReading(): HealthReadingContextValue {
  const ctx = React.useContext(HealthReadingContext);
  if (!ctx) throw new Error("useHealthReading must be used inside HealthReadingProvider");
  return ctx;
}
