import { api, ApiError } from "@/lib/api";
import type { GuildDetails } from "@/types/api";
import type { SystemHealthLike } from "@/lib/shellHealth";
import { deriveHealth } from "@/lib/shellHealth";
import {
  countLoggingEnabledWithoutChannel,
  countTicketCategoriesMissingStaff,
  deriveAttention,
  type AttentionItem,
} from "@/lib/deriveAttention";
import type { Status } from "@/components/ui/status";

export interface ModuleRow {
  key: string;
  name: string;
  status: Status;
  statusLabel: string;
  detail: string;
  href: string;
  error?: boolean;
}

export interface OverviewPayload {
  guild: GuildDetails | null;
  guildError: string | null;
  botOnline: boolean;
  botLatencyMs: number | null;
  healthLevel: ReturnType<typeof deriveHealth>["level"];
  healthReasons: string[];
  systemHealth: SystemHealthLike | null;
  requiredOk: number;
  requiredTotal: number;
  postgresConnected: boolean | null;
  postgresEnabled: boolean | null;
  schedulerRunning: boolean | null;
  attention: AttentionItem[];
  modules: ModuleRow[];
  accessLabel: string;
  grantsCount: number | null;
}

async function settled<T>(p: Promise<T>): Promise<{ ok: true; value: T } | { ok: false; error: unknown }> {
  try {
    return { ok: true, value: await p };
  } catch (e) {
    return { ok: false, error: e };
  }
}

function moduleStatus(on: boolean | null, configured?: boolean): { status: Status; label: string } {
  if (on === true) return { status: "online", label: "On" };
  if (on === false) return { status: "disabled", label: "Off" };
  if (configured) return { status: "warning", label: "Configured" };
  return { status: "unknown", label: "Unknown" };
}

export async function loadOverview(opts: {
  guildId: string;
  isRoot: boolean;
  userId: string;
}): Promise<OverviewPayload> {
  const { guildId, isRoot } = opts;
  const base = `/dashboard/guild/${guildId}`;

  const [
    guildRes,
    statusRes,
    healthRes,
    antinukeRes,
    automodRes,
    ticketsRes,
    welcomeRes,
    j2cRes,
    loggingRes,
    autoroleRes,
    rrRes,
    grantsRes,
  ] = await Promise.all([
    settled(api.getGuildDetails(guildId)),
    settled(api.getBotStatus()),
    settled(api.getSystemHealth(guildId)),
    settled(api.getAntiNuke(guildId)),
    settled(api.getAutomod(guildId)),
    settled(api.getTickets(guildId)),
    settled(api.getWelcome(guildId)),
    settled(api.getJ2C(guildId)),
    settled(api.getLogging(guildId)),
    settled(api.getAutoRole(guildId)),
    settled(api.getRR(guildId)),
    isRoot ? settled(api.listAccessGrants(guildId)) : Promise.resolve({ ok: false as const, error: null }),
  ]);

  const guild = guildRes.ok ? guildRes.value : null;
  const guildError =
    !guildRes.ok && guildRes.error instanceof ApiError
      ? guildRes.error.message
      : !guildRes.ok
        ? "Could not load server details."
        : null;

  const statusFailed = !statusRes.ok;
  const status = statusRes.ok ? statusRes.value : null;
  const systemHealth = healthRes.ok ? healthRes.value : null;
  const snapshot = deriveHealth({
    status: status ? { latency: status.latency } : null,
    statusFailed,
    health: systemHealth,
  });

  const requiredOk = systemHealth?.modules?.required_ok?.length ?? 0;
  const failed = systemHealth?.modules?.required_failed?.length ?? 0;
  const requiredTotal = requiredOk + failed;

  const antinukeStatus = antinukeRes.ok ? Boolean(antinukeRes.value?.status) : null;
  const loggingCfg = loggingRes.ok ? loggingRes.value : null;
  const ticketsCfg = ticketsRes.ok ? ticketsRes.value : null;

  const attention = deriveAttention({
    guildId,
    health: systemHealth,
    antinukeStatus,
    loggingPartial: loggingCfg
      ? {
          enabledWithoutChannel: countLoggingEnabledWithoutChannel(
            loggingCfg.log_enabled,
            loggingCfg.log_channels,
          ),
        }
      : null,
    ticketsGap: ticketsCfg
      ? {
          categoriesMissingStaff: countTicketCategoriesMissingStaff(ticketsCfg.categories),
        }
      : null,
  });

  const modules: ModuleRow[] = [];

  if (antinukeRes.ok) {
    const wl = antinukeRes.value?.whitelisted_users?.length ?? 0;
    const st = moduleStatus(antinukeStatus);
    modules.push({
      key: "antinuke",
      name: "Antinuke",
      status: st.status,
      statusLabel: st.label,
      detail: antinukeStatus ? `${wl} whitelisted user${wl === 1 ? "" : "s"}` : "—",
      href: `${base}/antinuke`,
    });
  } else {
    modules.push({
      key: "antinuke",
      name: "Antinuke",
      status: "unknown",
      statusLabel: "Unavailable",
      detail: "Could not load configuration.",
      href: `${base}/antinuke`,
      error: true,
    });
  }

  if (automodRes.ok) {
    const rules = Object.keys(automodRes.value.punishments ?? {}).length;
    const st = moduleStatus(automodRes.value.enabled);
    modules.push({
      key: "automod",
      name: "Automod",
      status: st.status,
      statusLabel: st.label,
      detail: automodRes.value.enabled ? `${rules} rule${rules === 1 ? "" : "s"}` : "—",
      href: `${base}/automod`,
    });
  } else {
    modules.push({
      key: "automod",
      name: "Automod",
      status: "unknown",
      statusLabel: "Unavailable",
      detail: "Could not load configuration.",
      href: `${base}/automod`,
      error: true,
    });
  }

  if (ticketsRes.ok) {
    const cats = ticketsCfg?.categories?.length ?? 0;
    const open = ticketsCfg?.open_ticket_count ?? 0;
    const configured = cats > 0 || Boolean(ticketsCfg?.panel_channel);
    const st = moduleStatus(null, configured);
    modules.push({
      key: "tickets",
      name: "Tickets",
      status: st.status,
      statusLabel: configured ? "Configured" : "Not configured",
      detail: configured ? `${cats} categor${cats === 1 ? "y" : "ies"} · ${open} open` : "—",
      href: `${base}/tickets`,
    });
  } else {
    modules.push({
      key: "tickets",
      name: "Tickets",
      status: "unknown",
      statusLabel: "Unavailable",
      detail: "Could not load configuration.",
      href: `${base}/tickets`,
      error: true,
    });
  }

  if (welcomeRes.ok) {
    const w = welcomeRes.value;
    const on = Boolean(w?.channel_id || w?.welcome_message);
    const st = moduleStatus(on);
    modules.push({
      key: "welcome",
      name: "Welcome",
      status: st.status,
      statusLabel: st.label,
      detail: on ? "Channel or message set" : "—",
      href: `${base}/welcome`,
    });
  }

  if (j2cRes.ok) {
    const j = j2cRes.value;
    const on = Boolean(j?.enabled ?? j?.status);
    const st = moduleStatus(on);
    modules.push({
      key: "j2c",
      name: "Join to Create",
      status: st.status,
      statusLabel: st.label,
      detail: on ? "Voice channel creation enabled" : "—",
      href: `${base}/j2c`,
    });
  }

  if (loggingRes.ok && loggingCfg) {
    const enabled = Object.values(loggingCfg.log_enabled ?? {}).filter(Boolean).length;
    const routed = Object.entries(loggingCfg.log_enabled ?? {}).filter(
      ([k, on]) => on && loggingCfg.log_channels?.[k],
    ).length;
    const partial = enabled > 0 && routed < enabled;
    modules.push({
      key: "logging",
      name: "Logging",
      status: partial ? "degraded" : enabled > 0 ? "online" : "disabled",
      statusLabel: partial ? "Partial" : enabled > 0 ? "On" : "Off",
      detail: enabled > 0 ? `${routed} of ${enabled} categories routed` : "—",
      href: `${base}/logging`,
    });
  }

  if (autoroleRes.ok) {
    const humans = autoroleRes.value.humans?.length ?? 0;
    const bots = autoroleRes.value.bots?.length ?? 0;
    const on = humans + bots > 0;
    const st = moduleStatus(on);
    modules.push({
      key: "autorole",
      name: "Auto role",
      status: st.status,
      statusLabel: st.label,
      detail: on ? `${humans} human · ${bots} bot role${bots === 1 ? "" : "s"}` : "—",
      href: `${base}/autorole`,
    });
  }

  if (rrRes.ok) {
    const list = Array.isArray(rrRes.value) ? rrRes.value : rrRes.value?.panels ?? rrRes.value?.roles ?? [];
    const count = Array.isArray(list) ? list.length : 0;
    const st = moduleStatus(count > 0);
    modules.push({
      key: "reactionroles",
      name: "Reaction roles",
      status: st.status,
      statusLabel: st.label,
      detail: count > 0 ? `${count} panel${count === 1 ? "" : "s"}` : "—",
      href: `${base}/reactionroles`,
    });
  }

  let accessLabel = "Dashboard access";
  if (isRoot) accessLabel = "Root owner";
  else if (grantsRes.ok && Array.isArray(grantsRes.value)) {
    const grantList = grantsRes.value as { discord_user_id?: string; template_key?: string; role?: string }[];
    const mine = grantList.find((g) => String(g.discord_user_id) === opts.userId);
    if (mine?.role) accessLabel = mine.role;
    else if (mine?.template_key) accessLabel = mine.template_key.charAt(0).toUpperCase() + mine.template_key.slice(1);
  }

  const grantsCount =
    grantsRes.ok && Array.isArray(grantsRes.value) ? grantsRes.value.length : isRoot ? null : null;

  return {
    guild,
    guildError,
    botOnline: !statusFailed && Boolean(status),
    botLatencyMs: snapshot.latencyMs,
    healthLevel: snapshot.level,
    healthReasons: snapshot.reasons,
    systemHealth,
    requiredOk,
    requiredTotal,
    postgresConnected: systemHealth?.postgres?.connected ?? null,
    postgresEnabled: systemHealth?.postgres?.enabled ?? null,
    schedulerRunning: systemHealth?.scheduler?.worker_running ?? null,
    attention,
    modules,
    accessLabel,
    grantsCount,
  };
}
