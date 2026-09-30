/**
 * Post–Discord OAuth routing (DS §14). Does not perform auth; only maps grants to paths.
 */

const DASHBOARD_PREFIX = "/dashboard";

export function isSafeDashboardCallback(path: string | null | undefined): path is string {
  if (!path || typeof path !== "string") return false;
  if (!path.startsWith(DASHBOARD_PREFIX)) return false;
  if (path.startsWith("//") || path.includes("://") || path.includes("\\")) return false;
  if (path.includes("..")) return false;
  return true;
}

function guildIdFromDashboardPath(path: string): string | null {
  const m = path.match(/^\/dashboard\/guild\/(\d{17,20})(?:\/|$)/);
  return m?.[1] ?? null;
}

function looksLikeGuildPath(path: string): boolean {
  return /^\/dashboard\/guild\//.test(path);
}

export function resolvePostAuthDestination(opts: {
  guildIds: string[];
  isRoot: boolean;
  callbackUrl?: string | null;
}): string {
  const { guildIds, isRoot, callbackUrl } = opts;

  if (isSafeDashboardCallback(callbackUrl)) {
    if (isRoot) return callbackUrl;

    const gid = guildIdFromDashboardPath(callbackUrl);
    if (gid) {
      if (guildIds.includes(gid)) return callbackUrl;
    } else if (!looksLikeGuildPath(callbackUrl)) {
      if (!callbackUrl.startsWith("/dashboard/admin")) {
        return callbackUrl;
      }
    }
  }

  if (guildIds.length === 0 && !isRoot) return "/auth/no-access";
  if (guildIds.length === 0 && isRoot) return "/dashboard/admin";
  if (guildIds.length === 1) return `/dashboard/guild/${guildIds[0]}`;
  return "/dashboard/guilds";
}
