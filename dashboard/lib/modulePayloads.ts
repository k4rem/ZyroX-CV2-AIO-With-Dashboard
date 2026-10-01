/**
 * Save payloads for Join to Create and Custom Roles.
 * Role and channel IDs stay decimal strings. Disabling J2C does not clear them.
 */

export interface J2CDraft {
  enabled: boolean;
  join_channel_id: string | null;
  control_channel_id: string | null;
  category_id: string | null;
}

export function buildJ2CUpdate(draft: J2CDraft) {
  return {
    enabled: draft.enabled,
    join_channel_id: draft.join_channel_id,
    control_channel_id: draft.control_channel_id,
    category_id: draft.category_id,
  };
}

export function j2cDraftFromApi(config: {
  enabled?: boolean | null;
  join_channel_id?: string | null;
  control_channel_id?: string | null;
  category_id?: string | null;
}): J2CDraft {
  const id = (value: string | null | undefined) => (typeof value === "string" && value.trim() ? value : null);
  const join = id(config.join_channel_id);
  const control = id(config.control_channel_id);
  const category = id(config.category_id);
  const enabled = config.enabled == null ? Boolean(join) : Boolean(config.enabled);
  return { enabled, join_channel_id: join, control_channel_id: control, category_id: category };
}

export const CUSTOM_ROLE_KEYS = ["reqrole", "staff", "girl", "vip", "guest", "frnd"] as const;
export type CustomRoleKey = (typeof CUSTOM_ROLE_KEYS)[number];

export const CUSTOM_ROLE_COMMANDS: { key: Exclude<CustomRoleKey, "reqrole">; name: string }[] = [
  { key: "staff", name: "staff" },
  { key: "girl", name: "girl" },
  { key: "vip", name: "vip" },
  { key: "guest", name: "guest" },
  { key: "frnd", name: "frnd" },
];

const SNOWFLAKE = /^\d{17,20}$/;

/** Accept only a string snowflake. Numbers are refused so parseInt cannot round them. */
export function roleIdFromApi(value: unknown): string | null {
  if (typeof value !== "string") return null;
  const trimmed = value.trim();
  return SNOWFLAKE.test(trimmed) ? trimmed : null;
}

export function customRolesDraftFromApi(config: Record<string, unknown>): Record<CustomRoleKey, string | null> {
  return {
    reqrole: roleIdFromApi(config.reqrole),
    staff: roleIdFromApi(config.staff),
    girl: roleIdFromApi(config.girl),
    vip: roleIdFromApi(config.vip),
    guest: roleIdFromApi(config.guest),
    frnd: roleIdFromApi(config.frnd),
  };
}

export function buildCustomRolesUpdate(draft: Record<CustomRoleKey, string | null>) {
  const out: Record<CustomRoleKey, string | null> = {
    reqrole: null,
    staff: null,
    girl: null,
    vip: null,
    guest: null,
    frnd: null,
  };
  for (const key of CUSTOM_ROLE_KEYS) {
    const value = draft[key];
    if (value == null || value === "") {
      out[key] = null;
      continue;
    }
    if (typeof value !== "string" || !SNOWFLAKE.test(value)) {
      throw new TypeError(`${key} must stay a Discord snowflake string`);
    }
    out[key] = value;
  }
  return out;
}

export function rolePlace(
  roleId: string | null,
  roles: { id: string; position?: number | null }[],
): { rank: number; total: number } | null {
  if (!roleId) return null;
  const role = roles.find((item) => item.id === roleId);
  if (!role || typeof role.position !== "number" || !Number.isFinite(role.position)) return null;
  const position = role.position;
  const ranked = roles.filter((item) => typeof item.position === "number");
  const above = ranked.filter((item) => (item.position as number) > position).length;
  return { rank: above + 1, total: ranked.length };
}

export function roleSwatch(color: number | null | undefined): string | null {
  if (typeof color !== "number" || !Number.isFinite(color) || color <= 0) return null;
  return `#${Math.trunc(color).toString(16).padStart(6, "0").slice(-6)}`;
}

export function draftsDiffer(a: unknown, b: unknown): boolean {
  return JSON.stringify(a) !== JSON.stringify(b);
}

export function isSaveShortcut(event: {
  key: string;
  metaKey: boolean;
  ctrlKey: boolean;
  altKey: boolean;
  shiftKey?: boolean;
}): boolean {
  return (event.key === "s" || event.key === "S") && (event.metaKey || event.ctrlKey) && !event.altKey && !event.shiftKey;
}

export function nextComboboxIndex(
  current: number,
  count: number,
  key: string,
): number | "select" | "close" | null {
  if (key === "Escape") return "close";
  if (key === "Enter") return count > 0 && current >= 0 ? "select" : null;
  if (count <= 0) return null;
  if (key === "ArrowDown") return current < 0 ? 0 : (current + 1) % count;
  if (key === "ArrowUp") return current < 0 ? count - 1 : (current - 1 + count) % count;
  if (key === "Home") return 0;
  if (key === "End") return count - 1;
  return null;
}
