export type AutomodRule = {
  id: string;
  name: string;
  enabled: boolean;
  engine: string;
  mode: "observe" | "enforce";
  trigger: Record<string, unknown>;
  scope: {
    include_channels: string[];
    exclude_channels: string[];
    include_categories: string[];
    exclude_categories: string[];
    exclude_roles: string[];
  };
  message_action: "keep" | "delete";
  member_action: "none" | "warn" | "timeout" | "kick" | "ban";
  timeout_seconds: number;
  notify_action: "none" | "dm" | "channel" | "both";
  points: number;
  last_triggered_at: string | null;
};

export type AutomodV2Config = {
  guild_id: string;
  enabled: boolean;
  preset: "relaxed" | "balanced" | "strict" | "custom";
  schema_version: number;
  exclusions: {
    channels: string[];
    categories: string[];
    roles: string[];
    members: string[];
    staff_roles: string[];
  };
  escalations: Array<{
    points: number;
    window_seconds: number;
    action: "timeout" | "kick" | "ban";
    duration_seconds: number | null;
  }>;
  strike_ttl_seconds: number;
  rules: AutomodRule[];
  migrated: boolean;
  migration_notes: string[];
  health: {
    status: "healthy" | "warning" | "error" | "locked" | "unavailable";
    checks: Array<{ id: string; label: string; ok: boolean; severity: "ok" | "warning" | "error" | "locked" | "unavailable"; fix_hint: string | null; scope: string }>;
    notes: string[];
  };
  native: { connected: boolean; label: string; detail?: string };
};

export function durationLabel(seconds: number): string {
  if (seconds % 86400 === 0) return `${seconds / 86400}d`;
  if (seconds % 3600 === 0) return `${seconds / 3600}h`;
  if (seconds % 60 === 0) return `${seconds / 60}m`;
  return `${seconds}s`;
}

export function actionSummary(rule: AutomodRule): string {
  const parts: string[] = [];
  if (rule.message_action === "delete") parts.push("Delete");
  else parts.push("Keep");
  if (rule.member_action === "timeout") parts.push(`Timeout ${durationLabel(rule.timeout_seconds)}`);
  else if (rule.member_action === "warn") parts.push("Warn");
  else if (rule.member_action === "kick") parts.push("Kick");
  else if (rule.member_action === "ban") parts.push("Ban");
  if (rule.notify_action === "dm") parts.push("DM");
  if (rule.notify_action === "channel") parts.push("Channel notice");
  if (rule.notify_action === "both") parts.push("DM + notice");
  return parts.join(" + ");
}

export function thresholdSummary(rule: AutomodRule): string {
  const trigger = rule.trigger;
  if (rule.id === "flood") return `${trigger.count} messages / ${trigger.window_seconds} sec`;
  if (rule.id === "duplicate") return `${trigger.count} repeats / ${trigger.window_seconds} sec`;
  if (rule.id === "caps") return `${trigger.percent}% caps · min ${trigger.min_length}`;
  if (rule.id === "mentions") return `${trigger.count} mentions`;
  if (rule.id === "emoji") return `${trigger.count} emoji`;
  if (rule.id === "links") return trigger.mode === "allow" ? "Allow list" : "Block links";
  if (rule.id === "invites") return "Block external invites";
  if (rule.id === "bad_words") return `${(trigger.terms as unknown[] | undefined)?.length || 0} words`;
  if (rule.id === "attachments") return String(trigger.policy || "allow").replaceAll("_", " ");
  if (rule.id === "keyword") return `${(trigger.phrases as unknown[] | undefined)?.length || 0} phrases`;
  return rule.name;
}

export function exclusionSummary(rule: AutomodRule): number {
  return Object.values(rule.scope).reduce((sum, list) => sum + list.length, 0);
}
