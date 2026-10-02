/** Client mirror of bot/cls_platform/health/contract.py. Cached fields only. */

export type HealthStatus = "healthy" | "warning" | "error" | "locked" | "unavailable";
export type HealthSeverity = "ok" | "warning" | "error" | "locked" | "unavailable";

export type HealthCheck = {
  id: string;
  label: string;
  ok: boolean;
  severity: HealthSeverity;
  fix_hint: string | null;
  scope: string;
};

export type ModuleHealth = {
  status: HealthStatus;
  checks: HealthCheck[];
};

export const HEALTH_LABEL: Record<HealthStatus, string> = {
  healthy: "Healthy",
  warning: "Needs attention",
  error: "Missing permission",
  locked: "Locked",
  unavailable: "Unavailable",
};

const CAPABILITIES: Record<string, [string, string]> = {
  manage_roles: ["Manage Roles", "Grant CLS the Manage Roles permission."],
  manage_messages: ["Manage Messages", "Grant CLS the Manage Messages permission."],
  moderate_members: ["Moderate Members", "Grant CLS the Moderate Members permission."],
  kick_members: ["Kick Members", "Grant CLS the Kick Members permission."],
  ban_members: ["Ban Members", "Grant CLS the Ban Members permission."],
  manage_channels: ["Manage Channels", "Grant CLS the Manage Channels permission."],
  view_audit_log: ["View Audit Log", "Grant CLS the View Audit Log permission."],
  send_messages: ["Send Messages", "Allow CLS to send messages here."],
  embed_links: ["Embed Links", "Allow CLS to embed links here."],
  attach_files: ["Attach Files", "Allow CLS to attach files here."],
  view_channel: ["Channel visibility", "Allow CLS to view this channel."],
  role_managed: ["Managed role", "Choose a role that is not managed by an integration."],
  role_hierarchy: ["Role above CLS", "Move the CLS role above this role."],
};

export const CHANNEL_CAPABILITIES = [
  "view_channel",
  "send_messages",
  "embed_links",
  "attach_files",
  "manage_channels",
] as const;

export type ChannelCapability = (typeof CHANNEL_CAPABILITIES)[number];

const CHANNEL_FAIL_LABELS: Record<ChannelCapability, string> = {
  view_channel: "Cannot view",
  send_messages: "Cannot send",
  embed_links: "Cannot embed",
  attach_files: "Cannot attach files",
  manage_channels: "Cannot manage channel",
};

export type ChannelCapabilities = Partial<Record<ChannelCapability, boolean>>;

export function healthCheck(input: {
  id: string;
  ok: boolean;
  severity: HealthSeverity;
  scope: string;
  label?: string;
  fix_hint?: string | null;
}): HealthCheck {
  const known = CAPABILITIES[input.id];
  const passed = Boolean(input.ok);
  return {
    id: input.id,
    label: input.label ?? known?.[0] ?? input.id,
    ok: passed,
    severity: passed ? "ok" : input.severity,
    fix_hint: passed ? null : input.fix_hint !== undefined ? input.fix_hint : known?.[1] ?? null,
    scope: input.scope,
  };
}

export function rollup(checks: HealthCheck[]): HealthStatus {
  if (checks.length === 0) return "unavailable";
  const failing = checks.filter((row) => !row.ok);
  if (failing.length === 0) return "healthy";
  const severities = new Set(failing.map((row) => row.severity));
  if (severities.has("error")) return "error";
  if (severities.has("unavailable")) return "unavailable";
  if (severities.has("warning")) return "warning";
  if (severities.has("locked")) return "locked";
  return "unavailable";
}

export function moduleHealth(checks: HealthCheck[]): ModuleHealth {
  return { status: rollup(checks), checks };
}

export function roleIsBelowBot(
  position: number,
  roleId: string | number,
  botPosition: number,
  botRoleId: string | number,
): boolean {
  if (Number(position) < Number(botPosition)) return true;
  if (Number(position) > Number(botPosition)) return false;
  return BigInt(roleId) < BigInt(botRoleId);
}

export function roleChecks(input: {
  managed: boolean;
  position?: number | null;
  roleId?: string | number | null;
  botPosition?: number | null;
  botRoleId?: string | number | null;
  manageRoles?: boolean | null;
}): HealthCheck[] {
  const rows: HealthCheck[] = [];
  if (input.manageRoles != null) {
    rows.push(healthCheck({ id: "manage_roles", ok: input.manageRoles, severity: "error", scope: "guild" }));
  }
  rows.push(healthCheck({ id: "role_managed", ok: !input.managed, severity: "warning", scope: "role" }));
  if (
    input.position != null &&
    input.roleId != null &&
    input.botPosition != null &&
    input.botRoleId != null
  ) {
    rows.push(
      healthCheck({
        id: "role_hierarchy",
        ok: roleIsBelowBot(input.position, input.roleId, input.botPosition, input.botRoleId),
        severity: "warning",
        scope: "role",
      }),
    );
  }
  return rows;
}

export function channelChecks(capabilities: ChannelCapabilities, required: ChannelCapability[]): HealthCheck[] {
  return required.map((key) =>
    healthCheck({
      id: key,
      ok: Boolean(capabilities[key]),
      severity: key === "embed_links" || key === "attach_files" ? "warning" : "error",
      scope: "channel",
      label: CHANNEL_FAIL_LABELS[key],
    }),
  );
}

export function failingSummary(checks: HealthCheck[]): string | null {
  const failing = checks.filter((row) => !row.ok);
  if (failing.length === 0) return null;
  return failing.map((row) => row.label).join(" · ");
}
