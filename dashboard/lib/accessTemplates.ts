/** Display labels for Phase 1 RBAC templates (matches bot cls_platform.capabilities). */

export const ACCESS_TEMPLATES: {
  key: string;
  label: string;
  description: string;
}[] = [
  {
    key: "admin",
    label: "Admin",
    description: "Configure modules, logging, security, tickets, and bot settings for this server.",
  },
  {
    key: "moderator",
    label: "Moderator",
    description: "Moderation, logging view, security view, tickets, and audit read access.",
  },
  {
    key: "support",
    label: "Support",
    description: "Tickets and logging view for support workflows.",
  },
];

export function templateLabel(key: string | undefined | null): string {
  if (!key) return "Custom";
  return ACCESS_TEMPLATES.find((t) => t.key === key)?.label ?? key;
}
