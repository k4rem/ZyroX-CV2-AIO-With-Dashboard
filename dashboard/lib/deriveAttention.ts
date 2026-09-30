/**
 * Overview "needs attention" items (DS §16.1). Pure — covered by node --test.
 */

import type { SystemHealthLike } from "@/lib/shellHealth";

export type AttentionSeverity = "critical" | "warning" | "info";

export interface AttentionItem {
  id: string;
  severity: AttentionSeverity;
  message: string;
  href: string;
}

export interface DeriveAttentionInput {
  guildId: string;
  health: SystemHealthLike | null;
  antinukeStatus: boolean | null;
  loggingPartial: { enabledWithoutChannel: number } | null;
  ticketsGap: { categoriesMissingStaff: number } | null;
}

export function deriveAttention(input: DeriveAttentionInput): AttentionItem[] {
  const { guildId, health, antinukeStatus, loggingPartial, ticketsGap } = input;
  const base = `/dashboard/guild/${guildId}`;
  const items: AttentionItem[] = [];

  for (const failed of health?.modules?.required_failed ?? []) {
    items.push({
      id: `module-failed-${failed.name}`,
      severity: "critical",
      message: `Required module failed: ${failed.name}${failed.error ? ` (${failed.error})` : ""}.`,
      href: base,
    });
  }

  const perm = health?.permissions?.guilds?.find((g) => g.guild_id === guildId);
  if (perm?.missing_by_module) {
    for (const [module, missing] of Object.entries(perm.missing_by_module)) {
      if (!missing?.length) continue;
      const route =
        module.toLowerCase().includes("log") ? `${base}/logging` :
        module.toLowerCase().includes("ticket") ? `${base}/tickets` :
        module.toLowerCase().includes("anti") ? `${base}/antinuke` :
        `${base}/settings`;
      items.push({
        id: `perm-${module}`,
        severity: "warning",
        message: `${module}: bot lacks ${missing.join(", ")}.`,
        href: route,
      });
    }
  }

  if (antinukeStatus === false) {
    items.push({
      id: "antinuke-off",
      severity: "info",
      message: "Antinuke is disabled.",
      href: `${base}/antinuke`,
    });
  }

  const logGap = loggingPartial?.enabledWithoutChannel ?? 0;
  if (logGap > 0) {
    items.push({
      id: "logging-partial",
      severity: "warning",
      message:
        logGap === 1
          ? "Logging: one category is enabled without a channel."
          : `Logging: ${logGap} categories are enabled without a channel.`,
      href: `${base}/logging`,
    });
  }

  const ticketGap = ticketsGap?.categoriesMissingStaff ?? 0;
  if (ticketGap > 0) {
    items.push({
      id: "tickets-staff",
      severity: "warning",
      message:
        ticketGap === 1
          ? "Tickets: one category has no staff roles assigned."
          : `Tickets: ${ticketGap} categories have no staff roles assigned.`,
      href: `${base}/tickets`,
    });
  }

  return items;
}

/** Count logging categories that are on but have no destination channel. */
export function countLoggingEnabledWithoutChannel(
  logEnabled: Record<string, boolean> | undefined,
  logChannels: Record<string, string> | undefined,
): number {
  if (!logEnabled) return 0;
  let n = 0;
  for (const [key, on] of Object.entries(logEnabled)) {
    if (!on) continue;
    const ch = logChannels?.[key];
    if (ch == null || ch === "" || ch === "0") n += 1;
  }
  return n;
}

/** Categories with empty staff_roles array. */
export function countTicketCategoriesMissingStaff(
  categories: { staff_roles?: string[] }[] | undefined,
): number {
  if (!categories?.length) return 0;
  return categories.filter((c) => !c.staff_roles || c.staff_roles.length === 0).length;
}
