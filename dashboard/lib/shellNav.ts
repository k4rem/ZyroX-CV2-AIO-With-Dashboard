/**
 * CLS OS dashboard navigation model (DS §15.2).
 *
 * Pure data + pure functions so it can be unit-tested with `node --test`
 * (no React, no path aliases, no icon imports). The shell maps `icon` keys to
 * Lucide components in components/shell/nav-icons.ts.
 *
 * Phase 1.5 rules encoded here:
 *  - Only routes that exist and are meaningful appear in navigation.
 *  - Verification and Leveling stay routable but are not surfaced (D26).
 *  - Root-only entries are emitted only when the server says `isRoot`.
 */

export type NavIconKey =
  | "overview"
  | "servers"
  | "roles"
  | "tickets"
  | "welcome"
  | "autorole"
  | "reactionroles"
  | "autoreact"
  | "invites"
  | "j2c"
  | "automod"
  | "logging"
  | "messages"
  | "antinuke"
  | "settings"
  | "access"
  | "platform"
  | "verification"
  | "leveling";

export type NavGroupId =
  | "overview"
  | "management"
  | "tickets"
  | "engagement"
  | "moderation"
  | "security"
  | "system";

export interface NavRoute {
  /** Path under `/dashboard/guild/{id}` ("" = overview) or an absolute `/dashboard/...` path. */
  path: string;
  label: string;
}

export interface NavItemDef {
  id: string;
  label: string;
  icon: NavIconKey;
  group: NavGroupId;
  scope: "guild" | "global";
  /** Routes owned by this item. The first route is the link target. */
  routes: NavRoute[];
  rootOnly?: boolean;
  /** Routable but never rendered in navigation. */
  hidden?: boolean;
  /** Shown only when no guild is selected (e.g. the server picker). */
  noGuildOnly?: boolean;
}

export const NAV_GROUP_LABELS: Record<NavGroupId, string> = {
  overview: "Overview",
  management: "Management",
  tickets: "Tickets",
  engagement: "Engagement",
  moderation: "Moderation",
  security: "Security",
  system: "System",
};

export const NAV_GROUP_ORDER: NavGroupId[] = [
  "overview",
  "management",
  "tickets",
  "engagement",
  "moderation",
  "security",
  "system",
];

export const NAV_ITEMS: NavItemDef[] = [
  {
    id: "overview",
    label: "Overview",
    icon: "overview",
    group: "overview",
    scope: "guild",
    routes: [{ path: "", label: "Overview" }],
  },
  {
    id: "servers",
    label: "Servers",
    icon: "servers",
    group: "overview",
    scope: "global",
    noGuildOnly: true,
    routes: [{ path: "/dashboard/guilds", label: "Servers" }],
  },
  {
    id: "roles",
    label: "Roles",
    icon: "roles",
    group: "management",
    scope: "guild",
    routes: [
      { path: "/customroles", label: "Custom roles" },
      { path: "/invcrole", label: "Voice role" },
      { path: "/vanityroles", label: "Vanity roles" },
    ],
  },
  {
    id: "tickets",
    label: "Tickets",
    icon: "tickets",
    group: "tickets",
    scope: "guild",
    routes: [
      { path: "/tickets", label: "Queue" },
      { path: "/tickets/panels", label: "Panels" },
      { path: "/tickets/categories", label: "Categories & Teams" },
      { path: "/tickets/settings", label: "Settings" },
      { path: "/tickets/transcripts", label: "Transcripts" },
    ],
  },
  {
    id: "welcome",
    label: "Welcome",
    icon: "welcome",
    group: "engagement",
    scope: "guild",
    routes: [{ path: "/welcome", label: "Welcome" }],
  },
  {
    id: "messages",
    label: "Messages",
    icon: "messages",
    group: "engagement",
    scope: "guild",
    routes: [{ path: "/messages", label: "Messages" }],
  },
  {
    id: "autorole",
    label: "Role Automation",
    icon: "autorole",
    group: "engagement",
    scope: "guild",
    routes: [{ path: "/autorole", label: "Role Automation" }],
  },
  {
    id: "reactionroles",
    label: "Role Menus",
    icon: "reactionroles",
    group: "engagement",
    scope: "guild",
    routes: [
      { path: "/reactionroles", label: "Menus" },
      { path: "/reactionroles/new", label: "Create" },
    ],
  },
  {
    id: "autoreact",
    label: "Auto react",
    icon: "autoreact",
    group: "engagement",
    scope: "guild",
    routes: [{ path: "/autoreact", label: "Auto react" }],
  },
  {
    id: "invites",
    label: "Invites",
    icon: "invites",
    group: "engagement",
    scope: "guild",
    routes: [
      { path: "/tracking", label: "Tracking" },
      { path: "/invites", label: "Invites" },
    ],
  },
  {
    id: "giveaways",
    label: "Giveaways",
    icon: "invites",
    group: "engagement",
    scope: "guild",
    routes: [{ path: "/giveaways", label: "Giveaways" }],
  },
  {
    id: "j2c",
    label: "Join to Create",
    icon: "j2c",
    group: "engagement",
    scope: "guild",
    routes: [{ path: "/j2c", label: "Join to Create" }],
  },
  {
    id: "commands",
    label: "Commands",
    icon: "settings",
    group: "moderation",
    scope: "guild",
    routes: [{ path: "/commands", label: "Commands" }],
  },
  {
    id: "automod",
    label: "Automod",
    icon: "automod",
    group: "moderation",
    scope: "guild",
    routes: [{ path: "/automod", label: "Automod" }],
  },
  {
    id: "logging",
    label: "Logging",
    icon: "logging",
    group: "moderation",
    scope: "guild",
    routes: [{ path: "/logging", label: "Logging" }],
  },
  {
    // Hidden until Verification V2 exists (Phase 3). Route and source are kept.
    id: "verification",
    label: "Verification",
    icon: "verification",
    group: "moderation",
    scope: "guild",
    hidden: true,
    routes: [{ path: "/verification", label: "Verification" }],
  },
  {
    // Not a planned CLS module; legacy source stays routable, never surfaced.
    id: "leveling",
    label: "Leveling",
    icon: "leveling",
    group: "engagement",
    scope: "guild",
    hidden: true,
    routes: [
      { path: "/leveling", label: "Leveling" },
      { path: "/leveling/leaderboard", label: "Leaderboard" },
    ],
  },
  {
    id: "antinuke",
    label: "Protection",
    icon: "antinuke",
    group: "security",
    scope: "guild",
    routes: [{ path: "/antinuke", label: "Protection" }],
  },
  {
    id: "recovery",
    label: "Recovery",
    icon: "settings",
    group: "system",
    scope: "guild",
    rootOnly: true,
    routes: [{ path: "/recovery", label: "Recovery" }],
  },
  {
    id: "config-transfer",
    label: "Backup & Transfer",
    icon: "settings",
    group: "system",
    scope: "guild",
    routes: [{ path: "/config-transfer", label: "Backup & Transfer" }],
  },
  {
    id: "settings",
    label: "Bot settings",
    icon: "settings",
    group: "system",
    scope: "guild",
    routes: [{ path: "/settings", label: "Bot settings" }],
  },
  {
    id: "access",
    label: "Access",
    icon: "access",
    group: "system",
    scope: "global",
    rootOnly: true,
    routes: [{ path: "/dashboard/access", label: "Access" }],
  },
  {
    id: "platform",
    label: "Platform",
    icon: "platform",
    group: "system",
    scope: "global",
    rootOnly: true,
    routes: [{ path: "/dashboard/admin", label: "Platform" }],
  },
];

export interface ResolvedNavItem {
  id: string;
  label: string;
  icon: NavIconKey;
  href: string;
  active: boolean;
}

export interface ResolvedNavGroup {
  id: NavGroupId;
  label: string;
  items: ResolvedNavItem[];
}

export interface ParsedPath {
  guildId: string | null;
  /** Path below the guild, e.g. "/antinuke" or "" for the overview. */
  subpath: string;
}

const GUILD_PATH = /^\/dashboard\/guild\/([^/]+)(\/.*)?$/;

export function parseDashboardPath(pathname: string): ParsedPath {
  const clean = pathname.replace(/\/+$/, "") || "/";
  const m = GUILD_PATH.exec(clean);
  if (!m) return { guildId: null, subpath: "" };
  return { guildId: m[1], subpath: m[2] ?? "" };
}

/**
 * Routes whose layout is composed for the full viewport width (AD §7). Everything
 * else keeps the `max-w-content` reading measure.
 */
export function isFluidRoute(pathname: string): boolean {
  const { guildId, subpath } = parseDashboardPath(pathname);
  return guildId !== null && (subpath === "" || subpath === "/tickets" || subpath.startsWith("/tickets/") || subpath === "/reactionroles" || subpath.startsWith("/reactionroles/") || subpath === "/autorole" || subpath.startsWith("/autorole/") || subpath === "/config-transfer");
}

export function guildBase(guildId: string): string {
  return `/dashboard/guild/${guildId}`;
}

function routeHref(item: NavItemDef, route: NavRoute, guildId: string | null): string {
  if (item.scope === "global") return route.path;
  return `${guildBase(guildId ?? "")}${route.path}`;
}

function routeMatches(route: NavRoute, pathname: string, item: NavItemDef, guildId: string | null): boolean {
  const target = routeHref(item, route, guildId);
  const clean = pathname.replace(/\/+$/, "") || "/";
  if (item.scope === "guild" && route.path === "") return clean === target;
  return clean === target || clean.startsWith(`${target}/`);
}

/** Longest-prefix match so `/leveling/leaderboard` wins over `/leveling`. */
function findMatchingRoute(
  pathname: string,
  guildId: string | null,
): { item: NavItemDef; route: NavRoute } | null {
  let best: { item: NavItemDef; route: NavRoute; len: number } | null = null;
  for (const item of NAV_ITEMS) {
    if (item.scope === "guild" && !guildId) continue;
    for (const route of item.routes) {
      if (routeMatches(route, pathname, item, guildId)) {
        const len = routeHref(item, route, guildId).length;
        if (!best || len > best.len) best = { item, route, len };
      }
    }
  }
  return best ? { item: best.item, route: best.route } : null;
}

export function buildNav(opts: {
  pathname: string;
  guildId: string | null;
  isRoot: boolean;
}): ResolvedNavGroup[] {
  const { pathname, guildId, isRoot } = opts;
  const match = findMatchingRoute(pathname, guildId);
  const groups: ResolvedNavGroup[] = [];

  for (const groupId of NAV_GROUP_ORDER) {
    const items: ResolvedNavItem[] = [];
    for (const item of NAV_ITEMS) {
      if (item.group !== groupId) continue;
      if (item.hidden) continue;
      if (item.rootOnly && !isRoot) continue;
      if (item.scope === "guild" && !guildId) continue;
      if (item.noGuildOnly && guildId) continue;
      items.push({
        id: item.id,
        label: item.label,
        icon: item.icon,
        href: routeHref(item, item.routes[0], guildId),
        active: match?.item.id === item.id,
      });
    }
    if (items.length > 0) {
      groups.push({ id: groupId, label: NAV_GROUP_LABELS[groupId], items });
    }
  }
  return groups;
}

export interface Crumb {
  label: string;
  href?: string;
  /** User/Discord-sourced text: render with dir="auto" (DS §26). */
  userContent?: boolean;
}

export function resolveBreadcrumbs(opts: {
  pathname: string;
  guildId: string | null;
  guildName?: string | null;
}): Crumb[] {
  const { pathname, guildId, guildName } = opts;
  const crumbs: Crumb[] = [];

  if (guildId) {
    crumbs.push({
      label: guildName || `Server ${guildId}`,
      href: guildBase(guildId),
      userContent: Boolean(guildName),
    });
  } else {
    crumbs.push({ label: "CLS OS", href: "/dashboard/guilds" });
  }

  const match = findMatchingRoute(pathname, guildId);
  if (!match) return crumbs;
  const { item, route } = match;

  if (item.id === "overview") {
    crumbs[crumbs.length - 1] = { ...crumbs[crumbs.length - 1], href: undefined };
    crumbs.push({ label: "Overview" });
    return crumbs;
  }

  if (item.id !== "servers") {
    crumbs.push({ label: NAV_GROUP_LABELS[item.group] });
  }
  if (item.routes.length > 1) {
    crumbs.push({ label: item.label, href: routeHref(item, item.routes[0], guildId) });
  }
  crumbs.push({ label: route.label });
  return crumbs;
}

/** Keep the same module when switching servers (A.6). */
export function switchGuildHref(pathname: string, nextGuildId: string): string {
  const { guildId, subpath } = parseDashboardPath(pathname);
  if (!guildId) return guildBase(nextGuildId);
  return `${guildBase(nextGuildId)}${subpath}`;
}
