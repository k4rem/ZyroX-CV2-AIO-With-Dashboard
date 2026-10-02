import { api, ApiError } from "@/lib/api";
import type { DiscordChannel, GuildDetails } from "@/types/api";
import type { SystemHealthLike } from "@/lib/shellHealth";
import { deriveHealth } from "@/lib/shellHealth";
import {
  countLoggingV2Gaps,
  countTicketCategoriesMissingStaff,
  deriveAttention,
  type AttentionItem,
} from "@/lib/deriveAttention";
import {
  channelComposition,
  j2cEnabled,
  j2cSteps,
  loggingV2Routing,
  permissionCoverage,
  permissionItems,
  rankAttention,
  requiredModuleItems,
  stepsDone,
  summarizeCoverage,
  ticketSteps,
  welcomeSteps,
  type ChannelKind,
  type ChecklistStep,
  type CoreItem,
  type CoverageBucket,
  type ModuleDomain,
  type PermissionCoverage,
} from "@/lib/overviewModel";
import type { Status } from "@/components/ui/status";

/** A discrete, real ratio drawn as a segment meter. */
export interface ModuleMeter {
  value: number;
  total: number;
  /** Text equivalent, always rendered next to the meter. */
  label: string;
  tone: "ok" | "warn" | "neutral";
  steps?: ChecklistStep[];
}

export interface ModuleRow {
  key: string;
  name: string;
  domain: ModuleDomain;
  status: Status;
  statusLabel: string;
  bucket: CoverageBucket;
  detail: string;
  meter?: ModuleMeter;
  href: string;
  error?: boolean;
}

export interface OverviewPayload {
  guild: GuildDetails | null;
  guildIconUrl: string | null;
  guildError: string | null;
  botOnline: boolean;
  botLatencyMs: number | null;
  healthLevel: ReturnType<typeof deriveHealth>["level"];
  healthReasons: string[];
  systemHealth: SystemHealthLike | null;
  requiredOkNames: string[];
  requiredFailedNames: string[];
  permissions: PermissionCoverage;
  /** System Core outer ring: one item per required module. `null` = not reported. */
  coreModules: CoreItem[] | null;
  /** System Core inner ring: one item per module permission requirement. `null` = not reported. */
  corePermissions: CoreItem[] | null;
  postgresConnected: boolean | null;
  postgresEnabled: boolean | null;
  schedulerRunning: boolean | null;
  attention: AttentionItem[];
  modules: ModuleRow[];
  coverage: Record<CoverageBucket, number>;
  channels: { kind: ChannelKind; label: string; count: number }[] | null;
  prefix: string | null;
  accessLabel: string;
  grantsCount: number | null;
  /** ISO time the loader finished; shown as "Checked hh:mm:ss". */
  checkedAt: string;
}

async function settled<T>(p: Promise<T>): Promise<{ ok: true; value: T } | { ok: false; error: unknown }> {
  try {
    return { ok: true, value: await p };
  } catch (e) {
    return { ok: false, error: e };
  }
}

function bucketFor(status: Status, error?: boolean): CoverageBucket {
  if (error || status === "unknown") return "unavailable";
  if (status === "online" || status === "healthy") return "on";
  if (status === "degraded" || status === "warning") return "partial";
  return "off";
}

function plural(n: number, one: string, many = `${one}s`): string {
  return `${n} ${n === 1 ? one : many}`;
}

/** State from a checklist: all done → `onStatus`, some → Incomplete, none → `offLabel`. */
function checklistState(
  steps: ChecklistStep[],
  onStatus: Status,
  onLabel: string,
  offLabel: string,
): { status: Status; label: string } {
  const done = stepsDone(steps);
  if (done === steps.length) return { status: onStatus, label: onLabel };
  if (done === 0) return { status: "disabled", label: offLabel };
  return { status: "degraded", label: "Incomplete" };
}

function stepsMeter(steps: ChecklistStep[]): ModuleMeter {
  const done = stepsDone(steps);
  return {
    value: done,
    total: steps.length,
    label: `${done} of ${steps.length} steps`,
    tone: done === steps.length ? "ok" : done === 0 ? "neutral" : "warn",
    steps,
  };
}

function missingSentence(steps: ChecklistStep[]): string {
  const missing = steps.filter((s) => !s.done).map((s) => s.label.toLowerCase());
  if (missing.length === 0) return "";
  return `Needs ${missing.join(" and ")}`;
}

function unavailableRow(key: string, name: string, domain: ModuleDomain, href: string): ModuleRow {
  return {
    key,
    name,
    domain,
    status: "unknown",
    statusLabel: "Unavailable",
    bucket: "unavailable",
    detail: "Could not load configuration.",
    href,
    error: true,
  };
}

function guildIcon(guild: GuildDetails | null): string | null {
  const icon = guild?.icon;
  if (!icon) return null;
  if (icon.startsWith("http")) return icon;
  return `https://cdn.discordapp.com/icons/${guild.id}/${icon}.png?size=64`;
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
    channelsRes,
    prefixRes,
    grantsRes,
  ] = await Promise.all([
    settled(api.getGuildDetails(guildId)),
    settled(api.getBotStatus()),
    settled(api.getSystemHealth(guildId)),
    settled(api.getSecurity(guildId)),
    settled(api.getAutomod(guildId)),
    settled(api.getTicketsV2(guildId)),
    settled(api.getWelcome(guildId)),
    settled(api.getJ2C(guildId)),
    settled(api.getLoggingV2(guildId)),
    settled(api.getAutoRole(guildId)),
    settled(api.getRR(guildId)),
    settled(api.getChannels(guildId)),
    settled(api.getPrefix(guildId)),
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

  const channelList: DiscordChannel[] = channelsRes.ok && Array.isArray(channelsRes.value) ? channelsRes.value : [];
  const channelName = (id: string | null | undefined): string | null => {
    if (!id) return null;
    const c = channelList.find((ch) => String(ch.id) === String(id));
    return c ? c.name : null;
  };

  const antinukeStatus = antinukeRes.ok
    ? antinukeRes.value?.human_mode === "OFF"
      ? false
      : antinukeRes.value?.human_mode
        ? true
        : null
    : null;
  const loggingHome = loggingRes.ok ? loggingRes.value : null;
  const loggingRoutes = loggingHome?.routes ?? null;
  const ticketsRaw = ticketsRes.ok ? ticketsRes.value : null;
  const ticketsCfg = ticketsRaw
    ? {
        panel_channel: (ticketsRaw.panels || []).find((panel: { channel_id?: string | null }) => panel.channel_id)?.channel_id ?? null,
        categories: (ticketsRaw.categories || []).map((category: { staff_role_ids?: string[] }) => ({
          staff_roles: category.staff_role_ids || [],
        })),
        open_ticket_count: ticketsRaw.open_now ?? 0,
        degraded_open: ticketsRaw.degraded_open ?? 0,
      }
    : null;

  const attention = rankAttention(
    deriveAttention({
      guildId,
      health: systemHealth,
      antinukeStatus,
      loggingPartial: loggingRoutes
        ? { enabledWithoutChannel: countLoggingV2Gaps(loggingRoutes) }
        : null,
      ticketsGap: ticketsCfg
        ? { categoriesMissingStaff: countTicketCategoriesMissingStaff(ticketsCfg.categories) }
        : null,
    }),
  );

  const modules: ModuleRow[] = [];

  // Security
  if (antinukeRes.ok) {
    const wl = antinukeRes.value?.whitelisted_users?.length ?? 0;
    modules.push({
      key: "antinuke",
      name: "Antinuke",
      domain: "security",
      status: antinukeStatus ? "online" : "disabled",
      statusLabel: antinukeStatus ? "On" : "Off",
      bucket: antinukeStatus ? "on" : "off",
      detail: plural(wl, "whitelisted user"),
      href: `${base}/antinuke`,
    });
  } else modules.push(unavailableRow("antinuke", "Antinuke", "security", `${base}/antinuke`));

  // Moderation
  if (automodRes.ok) {
    const on = Boolean(automodRes.value.enabled);
    const rules = Object.keys(automodRes.value.punishments ?? {}).length;
    modules.push({
      key: "automod",
      name: "Automod",
      domain: "moderation",
      status: on ? "online" : "disabled",
      statusLabel: on ? "On" : "Off",
      bucket: on ? "on" : "off",
      detail: rules > 0 ? `${plural(rules, "punishment rule")} configured` : "No punishment rules configured",
      href: `${base}/automod`,
    });
  } else modules.push(unavailableRow("automod", "Automod", "moderation", `${base}/automod`));

  if (loggingHome) {
    const { enabled, routed } = loggingV2Routing(loggingRoutes);
    const partial = enabled > 0 && routed < enabled;
    const st: Status = enabled === 0 ? "disabled" : partial ? "degraded" : "online";
    modules.push({
      key: "logging",
      name: "Logging",
      domain: "moderation",
      status: st,
      statusLabel: enabled === 0 ? "Off" : partial ? "Incomplete" : "On",
      bucket: bucketFor(st),
      detail: enabled === 0 ? "No event categories enabled" : `${routed} of ${enabled} enabled categories have a channel`,
      meter:
        enabled > 0
          ? { value: routed, total: enabled, label: `${routed} of ${enabled} routed`, tone: partial ? "warn" : "ok" }
          : undefined,
      href: `${base}/logging`,
    });
  } else modules.push(unavailableRow("logging", "Logging", "moderation", `${base}/logging`));

  // Tickets
  if (ticketsCfg) {
    const steps = ticketSteps(ticketsCfg);
    const st = checklistState(steps, "healthy", "Configured", "Not set up");
    const cats = ticketsCfg.categories?.length ?? 0;
    const open = ticketsCfg.open_ticket_count ?? 0;
    const degraded = ticketsCfg.degraded_open ?? 0;
    const panel = channelName(ticketsCfg.panel_channel);
    const facts = [
      panel ? `#${panel}` : null,
      cats > 0 ? plural(cats, "category", "categories") : null,
      `${open} open`,
    ].filter(Boolean);
    modules.push({
      key: "tickets",
      name: "Tickets",
      domain: "tickets",
      status: degraded > 0 ? "warning" : st.status,
      statusLabel: degraded > 0 ? "Needs attention" : st.label,
      bucket: bucketFor(st.status),
      detail: stepsDone(steps) === 0 ? "No panel channel or categories yet" : facts.join(" · "),
      meter: stepsMeter(steps),
      href: `${base}/tickets`,
    });
  } else modules.push(unavailableRow("tickets", "Tickets", "tickets", `${base}/tickets`));

  // Engagement
  if (welcomeRes.ok) {
    const w = welcomeRes.value;
    const steps = welcomeSteps(w);
    const st = checklistState(steps, "online", "On", "Off");
    const ch = channelName(w?.channel_id);
    modules.push({
      key: "welcome",
      name: "Welcome",
      domain: "engagement",
      status: st.status,
      statusLabel: st.label,
      bucket: bucketFor(st.status),
      detail:
        stepsDone(steps) === steps.length
          ? `Sends ${w?.welcome_type === "embed" ? "an embed" : "a message"} to ${ch ? `#${ch}` : "the set channel"}`
          : missingSentence(steps),
      meter: stepsMeter(steps),
      href: `${base}/welcome`,
    });
  } else modules.push(unavailableRow("welcome", "Welcome", "engagement", `${base}/welcome`));

  if (j2cRes.ok) {
    const j = j2cRes.value;
    const on = j2cEnabled(j);
    const steps = j2cSteps(j);
    const join = channelName(j?.join_channel_id);
    modules.push({
      key: "j2c",
      name: "Join to Create",
      domain: "engagement",
      status: on ? "online" : "disabled",
      statusLabel: on ? "On" : "Off",
      bucket: on ? "on" : "off",
      detail: on
        ? `Join ${join ?? "the set voice channel"}${steps[1].done ? "" : " · control channel not set"}`
        : j?.enabled === false && typeof j?.join_channel_id === "string" && j.join_channel_id.trim()
          ? "Off — saved channels kept"
          : "No join channel set",
      meter: stepsMeter(steps),
      href: `${base}/j2c`,
    });
  } else modules.push(unavailableRow("j2c", "Join to Create", "engagement", `${base}/j2c`));

  if (autoroleRes.ok) {
    const humans = autoroleRes.value.humans?.length ?? 0;
    const bots = autoroleRes.value.bots?.length ?? 0;
    const on = humans + bots > 0;
    modules.push({
      key: "autorole",
      name: "Auto roles",
      domain: "engagement",
      status: on ? "online" : "disabled",
      statusLabel: on ? "On" : "Off",
      bucket: on ? "on" : "off",
      detail: on ? `${plural(humans, "member role")} · ${plural(bots, "bot role")}` : "No roles assigned on join",
      href: `${base}/autorole`,
    });
  } else modules.push(unavailableRow("autorole", "Auto roles", "engagement", `${base}/autorole`));

  if (rrRes.ok) {
    const list = Array.isArray(rrRes.value) ? rrRes.value : rrRes.value?.panels ?? rrRes.value?.roles ?? [];
    const count = Array.isArray(list) ? list.length : 0;
    const on = count > 0;
    modules.push({
      key: "reactionroles",
      name: "Reaction roles",
      domain: "engagement",
      status: on ? "online" : "disabled",
      statusLabel: on ? "On" : "Off",
      bucket: on ? "on" : "off",
      detail: on ? `${count} configured` : "No reaction roles set up",
      href: `${base}/reactionroles`,
    });
  } else modules.push(unavailableRow("reactionroles", "Reaction roles", "engagement", `${base}/reactionroles`));

  let accessLabel = "Dashboard access";
  if (isRoot) accessLabel = "Root owner";
  else if (grantsRes.ok && Array.isArray(grantsRes.value)) {
    const grantList = grantsRes.value as { discord_user_id?: string; template_key?: string; role?: string }[];
    const mine = grantList.find((g) => String(g.discord_user_id) === opts.userId);
    if (mine?.role) accessLabel = mine.role;
    else if (mine?.template_key) accessLabel = mine.template_key.charAt(0).toUpperCase() + mine.template_key.slice(1);
  }

  const grantsCount = grantsRes.ok && Array.isArray(grantsRes.value) ? grantsRes.value.length : null;

  return {
    guild,
    guildIconUrl: guildIcon(guild),
    guildError,
    botOnline: !statusFailed && Boolean(status),
    botLatencyMs: snapshot.latencyMs,
    healthLevel: snapshot.level,
    healthReasons: snapshot.reasons,
    systemHealth,
    requiredOkNames: systemHealth?.modules?.required_ok ?? [],
    requiredFailedNames: (systemHealth?.modules?.required_failed ?? []).map((f) => f.name),
    permissions: permissionCoverage(systemHealth, guildId),
    coreModules: requiredModuleItems(systemHealth),
    corePermissions: permissionItems(systemHealth, guildId),
    postgresConnected: systemHealth?.postgres?.connected ?? null,
    postgresEnabled: systemHealth?.postgres?.enabled ?? null,
    schedulerRunning: systemHealth?.scheduler?.worker_running ?? null,
    attention,
    modules,
    coverage: summarizeCoverage(modules.map((m) => m.bucket)),
    channels: channelsRes.ok ? channelComposition(channelList) : null,
    prefix: prefixRes.ok && typeof prefixRes.value?.prefix === "string" ? prefixRes.value.prefix : null,
    accessLabel,
    grantsCount,
    checkedAt: new Date().toISOString(),
  };
}
