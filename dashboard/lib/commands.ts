export interface CommandRow {
  name: string;
  module: string;
  category: string;
  description: string;
  usage: string;
  aliases: string[];
  cooldown: { rate: number; per: number } | null;
  permissions: string[];
  dangerous: boolean;
  protected: boolean;
  enabled: boolean;
  allowed_role_ids: string[];
  blocked_role_ids: string[];
  allowed_channel_ids: string[];
  blocked_channel_ids: string[];
}

export function restrictionSummary(row: Pick<CommandRow, "protected" | "enabled" | "allowed_role_ids" | "blocked_role_ids" | "allowed_channel_ids" | "blocked_channel_ids">) {
  if (row.protected) return "Protected";
  if (!row.enabled) return "Off";
  const parts: string[] = [];
  if (row.allowed_role_ids.length) parts.push(`${row.allowed_role_ids.length} allowed roles`);
  if (row.blocked_role_ids.length) parts.push(`${row.blocked_role_ids.length} blocked roles`);
  if (row.allowed_channel_ids.length) parts.push(`${row.allowed_channel_ids.length} channels`);
  if (row.blocked_channel_ids.length) parts.push(`${row.blocked_channel_ids.length} excluded channels`);
  return parts.length ? parts.join(" · ") : "Everyone";
}

export function filterCommands(rows: CommandRow[], query: string, category: string, enabled: "all" | "on" | "off") {
  const needle = query.trim().toLowerCase();
  return rows.filter((row) => {
    if (category && category !== "all" && row.category !== category) return false;
    if (enabled === "on" && !row.enabled) return false;
    if (enabled === "off" && row.enabled) return false;
    if (!needle) return true;
    const text = `${row.name} ${row.category} ${row.description} ${row.aliases.join(" ")}`.toLowerCase();
    return text.includes(needle);
  });
}

export function commandCategories(rows: CommandRow[]) {
  return Array.from(new Set(rows.map((row) => row.category))).sort((a, b) => a.localeCompare(b));
}
