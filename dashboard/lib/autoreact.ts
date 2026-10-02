export type AutoReactRule = {
  id: string;
  name: string;
  enabled: boolean;
  scope: "all" | "selected" | "excluded";
  channel_ids: string[];
  mode: "contains" | "exact" | "starts" | "ends";
  pattern: string;
  emojis: string[];
  health: string;
};

export function triggerSummary(rule: Pick<AutoReactRule, "mode" | "pattern">) {
  const label = { contains: "Contains", exact: "Exact", starts: "Starts with", ends: "Ends with" }[rule.mode];
  return `${label} “${rule.pattern || "…"}”`;
}

export function emptyRule(): Omit<AutoReactRule, "id" | "health"> {
  return { name: "", enabled: true, scope: "selected", channel_ids: [], mode: "contains", pattern: "", emojis: [] };
}
