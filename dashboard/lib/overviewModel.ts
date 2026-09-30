/**
 * Overview operations-deck model (Phase 1.6 Task A). Pure — covered by node --test.
 *
 * Every value here is derived from a field the bot API actually returns. Nothing is
 * estimated: a module without a checkable condition gets no ratio.
 */

import type { SystemHealthLike } from "@/lib/shellHealth";

export type ModuleDomain = "security" | "moderation" | "tickets" | "engagement";

export const DOMAIN_ORDER: ModuleDomain[] = ["security", "moderation", "tickets", "engagement"];

export const DOMAIN_LABELS: Record<ModuleDomain, string> = {
  security: "Security",
  moderation: "Moderation",
  tickets: "Tickets",
  engagement: "Engagement",
};

/** One condition the bot needs before a module does anything. */
export interface ChecklistStep {
  label: string;
  done: boolean;
}

export function stepsDone(steps: ChecklistStep[]): number {
  return steps.filter((s) => s.done).length;
}

function hasText(v: unknown): boolean {
  return typeof v === "string" && v.trim().length > 0;
}

// --- Join to Create --------------------------------------------------------
// GET /guilds/{id}/j2c returns only guild_id, join_channel_id, control_channel_id,
// category_id. There is no `enabled` field: the dashboard form and the bot both treat
// the module as on when a join channel is stored (disabling saves all three as null).

export interface J2CLike {
  join_channel_id?: string | null;
  control_channel_id?: string | null;
  category_id?: string | null;
}

export function j2cEnabled(cfg: J2CLike | null | undefined): boolean {
  return hasText(cfg?.join_channel_id);
}

export function j2cSteps(cfg: J2CLike | null | undefined): ChecklistStep[] {
  return [
    { label: "Join channel", done: hasText(cfg?.join_channel_id) },
    { label: "Control channel", done: hasText(cfg?.control_channel_id) },
  ];
}

// --- Welcome ---------------------------------------------------------------
// greet2 sends only when a channel is stored and the chosen format has content.

export interface WelcomeLike {
  welcome_type?: string | null;
  welcome_message?: string | null;
  channel_id?: string | null;
  embed_data?: { message?: string | null; title?: string | null; description?: string | null } | null;
}

export function welcomeSteps(cfg: WelcomeLike | null | undefined): ChecklistStep[] {
  const embed = cfg?.welcome_type === "embed";
  const content = embed
    ? hasText(cfg?.embed_data?.title) || hasText(cfg?.embed_data?.description) || hasText(cfg?.embed_data?.message)
    : hasText(cfg?.welcome_message);
  return [
    { label: "Channel", done: hasText(cfg?.channel_id) },
    { label: embed ? "Embed content" : "Message", done: content },
  ];
}

// --- Tickets ---------------------------------------------------------------

export interface TicketsLike {
  panel_channel?: string | null;
  categories?: { staff_roles?: unknown[] }[];
}

export function ticketSteps(cfg: TicketsLike | null | undefined): ChecklistStep[] {
  const cats = cfg?.categories ?? [];
  return [
    { label: "Panel channel", done: hasText(cfg?.panel_channel) },
    { label: "A ticket category", done: cats.length > 0 },
    {
      label: "Staff roles on every category",
      done: cats.length > 0 && cats.every((c) => Array.isArray(c.staff_roles) && c.staff_roles.length > 0),
    },
  ];
}

// --- Logging ---------------------------------------------------------------

export function loggingRouting(
  logEnabled: Record<string, boolean> | undefined,
  logChannels: Record<string, string> | undefined,
): { enabled: number; routed: number } {
  let enabled = 0;
  let routed = 0;
  for (const [key, on] of Object.entries(logEnabled ?? {})) {
    if (!on) continue;
    enabled += 1;
    const ch = logChannels?.[key];
    if (ch != null && ch !== "" && ch !== "0") routed += 1;
  }
  return { enabled, routed };
}

// --- Coverage (module state distribution) -----------------------------------

export type CoverageBucket = "on" | "partial" | "off" | "unavailable";

export const COVERAGE_ORDER: CoverageBucket[] = ["on", "partial", "off", "unavailable"];

export const COVERAGE_LABELS: Record<CoverageBucket, string> = {
  on: "On",
  partial: "Incomplete",
  off: "Off",
  unavailable: "Unavailable",
};

export function summarizeCoverage(buckets: CoverageBucket[]): Record<CoverageBucket, number> {
  const out: Record<CoverageBucket, number> = { on: 0, partial: 0, off: 0, unavailable: 0 };
  for (const b of buckets) out[b] += 1;
  return out;
}

// --- Channels by type -------------------------------------------------------
// Discord channel types: 0 text, 5 announcement, 2 voice, 13 stage, 4 category.

export type ChannelKind = "text" | "voice" | "category" | "other";

export const CHANNEL_KIND_LABELS: Record<ChannelKind, string> = {
  text: "Text",
  voice: "Voice",
  category: "Categories",
  other: "Other",
};

export function channelKind(type: string | number): ChannelKind {
  const t = String(type);
  if (t === "0" || t === "5") return "text";
  if (t === "2" || t === "13") return "voice";
  if (t === "4") return "category";
  return "other";
}

/** Non-zero kinds in a fixed order. */
export function channelComposition(
  channels: { type: string | number }[] | null | undefined,
): { kind: ChannelKind; label: string; count: number }[] {
  const counts: Record<ChannelKind, number> = { text: 0, voice: 0, category: 0, other: 0 };
  for (const c of channels ?? []) counts[channelKind(c.type)] += 1;
  return (Object.keys(counts) as ChannelKind[])
    .filter((k) => counts[k] > 0)
    .map((kind) => ({ kind, label: CHANNEL_KIND_LABELS[kind], count: counts[kind] }));
}

// --- Permissions ------------------------------------------------------------

export interface PermissionCoverage {
  known: boolean;
  /** Modules the bot declares permission requirements for. */
  total: number;
  /** Modules whose required permissions the bot currently has in this server. */
  satisfied: number;
  missingModules: string[];
}

export function permissionCoverage(health: SystemHealthLike | null, guildId: string): PermissionCoverage {
  const required = Object.keys(health?.permissions?.module_requirements ?? {});
  const entry = health?.permissions?.guilds?.find((g) => String(g.guild_id) === String(guildId));
  if (!entry || required.length === 0) {
    return { known: false, total: 0, satisfied: 0, missingModules: [] };
  }
  const missingModules = Object.entries(entry.missing_by_module ?? {})
    .filter(([, missing]) => (missing?.length ?? 0) > 0)
    .map(([module]) => module);
  const missingRequired = missingModules.filter((m) => required.includes(m)).length;
  return {
    known: true,
    total: required.length,
    satisfied: required.length - missingRequired,
    missingModules,
  };
}

// --- Attention ranking ------------------------------------------------------

const SEVERITY_RANK = { critical: 0, warning: 1, info: 2 } as const;

/** Stable: critical → warning → info, original order within a severity. */
export function rankAttention<T extends { severity: keyof typeof SEVERITY_RANK }>(items: T[]): T[] {
  return items
    .map((item, i) => ({ item, i }))
    .sort((a, b) => SEVERITY_RANK[a.item.severity] - SEVERITY_RANK[b.item.severity] || a.i - b.i)
    .map((x) => x.item);
}
