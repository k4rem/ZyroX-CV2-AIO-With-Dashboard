/**
 * Topbar health state (DS §15.3, §23). Pure so it can be tested with node --test.
 *
 * Only real Phase 1 responses go in. Nothing here invents a healthy state:
 * with no data yet the level is "loading", and any failed status call is "offline".
 */

export type HealthLevel = "loading" | "online" | "degraded" | "offline";

export interface BotStatusLike {
  latency: number;
}

export interface SystemHealthLike {
  postgres?: { enabled?: boolean; connected?: boolean };
  scheduler?: { worker_running?: boolean };
  modules?: {
    healthy?: boolean;
    required_ok?: string[];
    required_failed?: { name: string; error?: string }[];
  };
  permissions?: {
    guilds?: {
      guild_id: string;
      guild_name?: string;
      missing_by_module?: Record<string, string[]>;
      critical?: boolean;
    }[];
  };
}

export interface HealthInput {
  status: BotStatusLike | null;
  statusFailed: boolean;
  health: SystemHealthLike | null;
}

export interface HealthSnapshot {
  level: HealthLevel;
  latencyMs: number | null;
  /** Human-readable reasons behind a degraded level (empty when online). */
  reasons: string[];
}

export const DEGRADED_LATENCY_MS = 400;

export function deriveHealth(input: HealthInput): HealthSnapshot {
  const { status, statusFailed, health } = input;

  if (statusFailed) {
    return { level: "offline", latencyMs: null, reasons: ["Bot API unreachable"] };
  }
  if (!status) {
    return { level: "loading", latencyMs: null, reasons: [] };
  }

  const latencyMs = Number.isFinite(status.latency) ? Math.round(status.latency) : null;
  const reasons: string[] = [];

  if (latencyMs !== null && latencyMs > DEGRADED_LATENCY_MS) {
    reasons.push(`Gateway latency above ${DEGRADED_LATENCY_MS} ms`);
  }
  const failed = health?.modules?.required_failed ?? [];
  if (failed.length > 0) {
    reasons.push(`Required module failed: ${failed.map((f) => f.name).join(", ")}`);
  }
  if (health?.postgres?.enabled && health.postgres.connected === false) {
    reasons.push("Postgres not connected");
  }

  return {
    level: reasons.length > 0 ? "degraded" : "online",
    latencyMs,
    reasons,
  };
}

export interface GuildPermissionSummary {
  known: boolean;
  missingModules: { module: string; missing: string[] }[];
}

/** Permission health for one authorized guild only. Other guilds are never read. */
export function permissionSummaryForGuild(
  health: SystemHealthLike | null,
  guildId: string | null,
): GuildPermissionSummary {
  if (!health || !guildId) return { known: false, missingModules: [] };
  const entry = health.permissions?.guilds?.find((g) => g.guild_id === guildId);
  if (!entry) return { known: false, missingModules: [] };
  const missingModules = Object.entries(entry.missing_by_module ?? {}).map(([module, missing]) => ({
    module,
    missing,
  }));
  return { known: true, missingModules };
}
