/**
 * Dashboard API client — all traffic goes through same-origin /api/bot proxy.
 */

import type { SystemHealthLike } from "@/lib/shellHealth";
import {
  BotInfo,
  BotStatus,
  GuildSummary,
  GuildDetails,
  PrefixConfig,
  AutomodConfig,
  TicketConfig,
  LevelingConfig,
  LoggingConfig,
  PrefixUpdate,
  AutomodUpdate,
  LevelingUpdate,
  LoggingUpdate,
  LeaderboardEntry,
  DiscordChannel,
  DiscordRole,
  AutoRoleConfig,
  AutoRoleUpdate,
  AdminStats,
  AdminConfig,
  AdminConfigUpdate,
} from "@/types/api";

const BASE_URL = "/api/bot";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit & { next?: NextFetchRequestConfig } = {}
): Promise<T> {
  if (typeof window === "undefined") {
    const { serverBotRequest } = await import("@/lib/serverBotRequest");
    return serverBotRequest<T>(endpoint, options);
  }

  const url = `${BASE_URL}${endpoint}`;

  const headers = new Headers(options.headers);
  if (!(options.body instanceof FormData) && !headers.has("Content-Type") && options.body) {
    headers.set("Content-Type", "application/json");
  }

  const response = await fetch(url, {
    ...options,
    headers,
    credentials: "same-origin",
    next: options.next || { revalidate: 0 },
  });

  if (!response.ok) {
    let errorData: { detail?: string };
    try {
      errorData = await response.json();
    } catch {
      errorData = { detail: "An unknown error occurred" };
    }
    throw new ApiError(response.status, errorData.detail || response.statusText);
  }

  return response.json();
}

export const api = {
  getBotStatus: () => request<BotStatus>("/bot/status"),
  getBotInfo: () => request<BotInfo>("/bot/info"),
  getSystemHealth: (guildId?: string) =>
    request<SystemHealthLike>(
      `/system/health${guildId ? `?guild_id=${encodeURIComponent(guildId)}` : ""}`,
    ),

  listGuilds: () => request<GuildSummary[]>("/guilds/"),
  getGuildDetails: (guildId: string) => request<GuildDetails>(`/guilds/${guildId}`),
  getChannels: (guildId: string) => request<DiscordChannel[]>(`/guilds/${guildId}/channels`),
  getRoles: (guildId: string) => request<DiscordRole[]>(`/guilds/${guildId}/roles`),
  getRuntimeHealth: (guildId: string) =>
    request<import("@/lib/platformHealth").ModuleHealth & {
      bot: { top_role_id: string; top_role_position: number; manage_roles: boolean } | null;
      roles: Record<string, { position: number | null; managed: boolean; status: string }>;
      channels: Record<string, import("@/lib/platformHealth").ChannelCapabilities>;
    }>(`/guilds/${guildId}/runtime-health`),

  getPrefix: (guildId: string) => request<PrefixConfig>(`/guilds/${guildId}/prefix`),
  updatePrefix: (guildId: string, prefix: string) =>
    request<{ status: string; new_prefix: string }>(`/guilds/${guildId}/prefix`, {
      method: "POST",
      body: JSON.stringify({ prefix }),
    }),

  getAutomod: (guildId: string) => request<AutomodConfig>(`/guilds/${guildId}/automod`),
  updateAutomod: (guildId: string, data: Partial<AutomodConfig>) =>
    request<{ status: string }>(`/guilds/${guildId}/automod`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  getAutomodV2: (guildId: string) => request<import("@/lib/automodModel").AutomodV2Config>(`/guilds/${guildId}/automod/v2`),
  saveAutomodV2: (guildId: string, data: import("@/lib/automodModel").AutomodV2Config) =>
    request<import("@/lib/automodModel").AutomodV2Config>(`/guilds/${guildId}/automod/v2`, {
      method: "PUT",
      body: JSON.stringify(data),
    }),
  getAutomodOverview: (guildId: string) => request<any>(`/guilds/${guildId}/automod/v2/overview`),
  getAutomodPreset: (guildId: string, preset: string) => request<{ preset: string; rules: import("@/lib/automodModel").AutomodRule[] }>(`/guilds/${guildId}/automod/v2/presets/${preset}`),
  getAutomodViolations: (guildId: string, query: string) => request<any>(`/guilds/${guildId}/automod/v2/violations${query}`),
  getAutomodViolation: (guildId: string, id: string) => request<any>(`/guilds/${guildId}/automod/v2/violations/${id}`),
  markAutomodFalsePositive: (guildId: string, id: string) =>
    request<any>(`/guilds/${guildId}/automod/v2/violations/${id}/false-positive`, { method: "POST" }),
  applyAutomodFollowup: (guildId: string, id: string, body: { confirm: boolean; kind: string; value: string }) =>
    request<any>(`/guilds/${guildId}/automod/v2/violations/${id}/follow-up`, { method: "POST", body: JSON.stringify(body) }),
  getAutomodStrikes: (guildId: string) => request<{ rows: any[] }>(`/guilds/${guildId}/automod/v2/strikes`),
  testAutomodMessage: (guildId: string, content: string) =>
    request<{ matches: any[] }>(`/guilds/${guildId}/automod/v2/test`, { method: "POST", body: JSON.stringify({ content }) }),

  getTickets: (guildId: string) => request<TicketConfig>(`/guilds/${guildId}/tickets`),
  getTicketsV2: (guildId: string) => request<any>(`/guilds/${guildId}/tickets/v2`),
  createTicketCategory: (guildId: string, data: any) =>
    request<any>(`/guilds/${guildId}/tickets/v2/categories`, { method: "POST", body: JSON.stringify(data) }),
  createTicketPanel: (guildId: string, data: any) =>
    request<any>(`/guilds/${guildId}/tickets/v2/panels`, { method: "POST", body: JSON.stringify(data) }),
  getTicketTranscript: (guildId: string, ticketId: string) => request<any>(`/guilds/${guildId}/tickets/v2/${ticketId}`),
  updateTicketLimits: (guildId: string, data: { cooldown_seconds: number; max_open: number; auto_close_hours?: number | null; grace_minutes?: number; transcript_channel_id?: string | null; name_format?: string }) =>
    request<any>(`/guilds/${guildId}/tickets/v2/settings`, { method: "PATCH", body: JSON.stringify(data) }),
  updateTicketPanel: (guildId: string, panelId: string, data: any) =>
    request<any>(`/guilds/${guildId}/tickets/v2/panels/${panelId}`, { method: "PATCH", body: JSON.stringify(data) }),
  publishTicketPanel: (guildId: string, panelId: string, data: any) =>
    request<any>(`/guilds/${guildId}/tickets/v2/panels/${panelId}/publish`, { method: "POST", body: JSON.stringify(data) }),
  getTicketQueue: (guildId: string) => request<{ tickets: any[] }>(`/guilds/${guildId}/tickets/v2/queue`),
  getTicketDetail: (guildId: string, ticketId: string) => request<any>(`/guilds/${guildId}/tickets/v2/${ticketId}/detail`),
  actOnTicket: (guildId: string, ticketId: string, data: any) =>
    request<any>(`/guilds/${guildId}/tickets/v2/${ticketId}/action`, { method: "POST", body: JSON.stringify(data) }),
  getTicketPanel: (guildId: string, panelId: string) => request<any>(`/guilds/${guildId}/tickets/v2/panels/${panelId}`),
  saveTicketPanel: (guildId: string, panelId: string, data: any) =>
    request<any>(`/guilds/${guildId}/tickets/v2/panels/${panelId}`, { method: "PUT", body: JSON.stringify(data) }),
  duplicateTicketPanel: (guildId: string, panelId: string) =>
    request<any>(`/guilds/${guildId}/tickets/v2/panels/${panelId}/duplicate`, { method: "POST" }),
  deleteTicketPanel: (guildId: string, panelId: string) =>
    request<any>(`/guilds/${guildId}/tickets/v2/panels/${panelId}`, { method: "DELETE" }),
  updateTicketCategory: (guildId: string, categoryId: string, data: any) =>
    request<any>(`/guilds/${guildId}/tickets/v2/categories/${categoryId}`, { method: "PATCH", body: JSON.stringify(data) }),
  getTicketCategoryCounts: (guildId: string) => request<{ counts: Record<string, { open: number; total: number }> }>(`/guilds/${guildId}/tickets/v2/categories/summary`),
  getTicketBlocklist: (guildId: string) => request<{ blocked: any[] }>(`/guilds/${guildId}/tickets/v2/blacklist`),
  searchTicketMembers: (guildId: string, query: string) => request<{ members: any[] }>(`/guilds/${guildId}/tickets/v2/members?q=${encodeURIComponent(query)}`),
  getTicketTranscripts: (guildId: string) => request<{ transcripts: any[] }>(`/guilds/${guildId}/tickets/v2/transcripts`),
  getTicketTags: (guildId: string) => request<{ tags: Array<{ id: string; name: string; position: number }> }>(`/guilds/${guildId}/tickets/v2/tags`),
  createTicketTag: (guildId: string, data: { name: string; position?: number }) => request<any>(`/guilds/${guildId}/tickets/v2/tags`, { method: "POST", body: JSON.stringify(data) }),
  updateTicketTag: (guildId: string, tagId: string, data: { name: string; position?: number }) => request<any>(`/guilds/${guildId}/tickets/v2/tags/${tagId}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteTicketTag: (guildId: string, tagId: string) => request<any>(`/guilds/${guildId}/tickets/v2/tags/${tagId}`, { method: "DELETE" }),
  getTicketMetrics: (guildId: string, days: number) => request<any>(`/guilds/${guildId}/tickets/v2/metrics?days=${days}`),
  getTicketReplies: (guildId: string) => request<{ replies: Array<{ id: string; name: string; content: string }> }>(`/guilds/${guildId}/tickets/v2/replies`),
  createTicketReply: (guildId: string, data: { name: string; content: string }) => request<any>(`/guilds/${guildId}/tickets/v2/replies`, { method: "POST", body: JSON.stringify(data) }),
  deleteTicketReply: (guildId: string, replyId: string) => request<any>(`/guilds/${guildId}/tickets/v2/replies/${replyId}`, { method: "DELETE" }),
  blacklistTicketUser: (guildId: string, data: string | { user_id: string; reason?: string; display_name?: string; avatar?: string }) =>
    request<any>(`/guilds/${guildId}/tickets/v2/blacklist`, { method: "POST", body: JSON.stringify(typeof data === "string" ? { user_id: data } : data) }),
  unblacklistTicketUser: (guildId: string, userId: string) =>
    request<any>(`/guilds/${guildId}/tickets/v2/blacklist/${userId}`, { method: "DELETE" }),
  updateTickets: (guildId: string, data: any) =>
    request<{ status: string }>(`/guilds/${guildId}/tickets`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getLeveling: (guildId: string) => request<LevelingConfig>(`/guilds/${guildId}/leveling`),
  updateLeveling: (guildId: string, data: any) =>
    request<{ status: string }>(`/guilds/${guildId}/leveling`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getCommands: (guildId: string) => request<{ commands: any[] }>(`/guilds/${guildId}/commands`),
  updateCommand: (
    guildId: string,
    data: {
      command_name: string;
      enabled: boolean;
      allowed_role_ids: string[];
      blocked_role_ids: string[];
      allowed_channel_ids: string[];
      blocked_channel_ids: string[];
    },
  ) => request<any>(`/guilds/${guildId}/commands`, { method: "PUT", body: JSON.stringify(data) }),
  getLoggingV2: (guildId: string, query = "") => request<any>(`/guilds/${guildId}/logging/v2${query}`),
  getLoggingEvent: (guildId: string, eventId: string) => request<any>(`/guilds/${guildId}/logging/v2/events/${eventId}`),
  searchLoggingMembers: (guildId: string, query: string) =>
    request<{ members: Array<{ id: string; display_name: string; username: string | null; avatar_url: string | null }> }>(
      `/guilds/${guildId}/logging/v2/members?q=${encodeURIComponent(query)}`,
    ),
  updateLoggingRoute: (guildId: string, data: { category: string; enabled: boolean; channel_id: string | null }) =>
    request<any>(`/guilds/${guildId}/logging/v2/routes`, { method: "PUT", body: JSON.stringify(data) }),
  updateLoggingIgnores: (guildId: string, data: { channels: string[]; roles: string[]; users: string[] }) =>
    request<any>(`/guilds/${guildId}/logging/v2/ignores`, { method: "PUT", body: JSON.stringify(data) }),
  sendLoggingTest: (guildId: string, category: string) =>
    request<{ status: string; channel_id: string; route?: { category: string; enabled: boolean; channel_id: string | null; channel_name?: string | null; delivery?: string } }>(
      `/guilds/${guildId}/logging/v2/routes/${category}/test`,
      { method: "POST" },
    ),
  updateLoggingEventRoute: (guildId: string, eventType: string, data: { mode: string; channel_id: string | null }) =>
    request<any>(`/guilds/${guildId}/logging/v2/event-routes/${eventType}`, { method: "PUT", body: JSON.stringify(data) }),
  sendLoggingEventTest: (guildId: string, eventType: string) =>
    request<{ status: string; channel_id: string }>(`/guilds/${guildId}/logging/v2/event-routes/${eventType}/test`, { method: "POST" }),
  updateLoggingAppearance: (guildId: string, data: Record<string, unknown>) =>
    request<any>(`/guilds/${guildId}/logging/v2/appearance`, { method: "PUT", body: JSON.stringify(data) }),
  getLogging: (guildId: string) => request<LoggingConfig>(`/guilds/${guildId}/logging`),
  updateLogging: (guildId: string, data: any) =>
    request<{ status: string }>(`/guilds/${guildId}/logging`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getLeaderboard: (guildId: string) =>
    request<LeaderboardEntry[]>(`/guilds/${guildId}/leveling/leaderboard`),

  getWelcome: (guildId: string) => request<any>(`/guilds/${guildId}/welcome`),
  updateWelcome: (guildId: string, data: any) =>
    request<{ status: string }>(`/guilds/${guildId}/welcome`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  getWelcomeHome: (guildId: string) => request<any>(`/guilds/${guildId}/welcome/home`),
  saveWelcomeChannel: (guildId: string, data: any) =>
    request<any>(`/guilds/${guildId}/welcome/channel`, { method: "PUT", body: JSON.stringify(data) }),
  saveWelcomeDm: (guildId: string, data: any) =>
    request<any>(`/guilds/${guildId}/welcome/dm`, { method: "PUT", body: JSON.stringify(data) }),
  saveWelcomeGoodbye: (guildId: string, data: any) =>
    request<any>(`/guilds/${guildId}/welcome/goodbye`, { method: "PUT", body: JSON.stringify(data) }),
  sendWelcomeTest: (guildId: string, data: any) =>
    request<{ status: string }>(`/guilds/${guildId}/welcome/test`, { method: "POST", body: JSON.stringify(data) }),

  getAntiNuke: (guildId: string) => request<any>(`/guilds/${guildId}/antinuke`),
  updateAntiNuke: (guildId: string, data: any) =>
    request<{ status: string }>(`/guilds/${guildId}/antinuke`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),
  getSnapshots: (guildId: string) => request<any[]>(`/guilds/${guildId}/snapshots`),
  planRestore: (guildId: string, snapshotId: string, presentMemberIds: string[]) =>
    request<any>(`/guilds/${guildId}/snapshots/${snapshotId}/plan`, {
      method: "POST",
      body: JSON.stringify({ present_member_ids: presentMemberIds }),
    }),
  getSecurity: (guildId: string) => request<any>(`/guilds/${guildId}/security`),
  setSecurityMode: (
    guildId: string,
    data: { subsystem: string; mode: string; expected_version: number },
  ) =>
    request<{ human_mode: string; bot_mode: string; version: number }>(`/guilds/${guildId}/security/mode`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  releaseQuarantine: (guildId: string, userId: string) =>
    request<{ status: string }>(`/guilds/${guildId}/security/quarantine/${userId}/release`, { method: "POST" }),
  getSecurityIncident: (guildId: string, incidentId: string) =>
    request<any>(`/guilds/${guildId}/security/incidents/${incidentId}`),
  updateSecurityCenter: (guildId: string, data: { phishing_action?: string; trap_channel_ids?: string[] }) =>
    request<any>(`/guilds/${guildId}/security/center`, { method: "PUT", body: JSON.stringify(data) }),
  setDashboardLock: (guildId: string, locked: boolean) =>
    request<any>(`/guilds/${guildId}/security/lock`, { method: "POST", body: JSON.stringify({ locked }) }),

  getVerification: (guildId: string) => request<any>(`/guilds/${guildId}/verification`),
  updateVerification: (guildId: string, data: any) =>
    request<any>(`/guilds/${guildId}/verification`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getVanityRoles: (guildId: string) => request<unknown[]>(`/guilds/${guildId}/vanityroles`),
  addVanityRole: (guildId: string, data: any) =>
    request<{ status: string }>(`/guilds/${guildId}/vanityroles`, {
      method: "POST",
      body: JSON.stringify(data),
    }),
  deleteVanityRole: (guildId: string, vanity: string) =>
    request<{ status: string }>(`/guilds/${guildId}/vanityroles/${vanity}`, {
      method: "DELETE",
    }),

  getConfigPreview: (guildId: string) => request<{ groups: { id: string; label: string; modules: { id: string; label: string; summary: string }[] }[] }>(`/guilds/${guildId}/config-transfer/preview`),
  exportConfig: (guildId: string, modules: string[]) => request<any>(`/guilds/${guildId}/config-transfer/export`, { method: "POST", body: JSON.stringify({ modules }) }),
  validateConfig: (guildId: string, bundle: unknown) => request<any>(`/guilds/${guildId}/config-transfer/validate`, { method: "POST", body: JSON.stringify({ bundle }) }),
  planConfig: (guildId: string, body: any) => request<any>(`/guilds/${guildId}/config-transfer/plan`, { method: "POST", body: JSON.stringify(body) }),
  applyConfig: (guildId: string, body: any) => request<any>(`/guilds/${guildId}/config-transfer/apply`, { method: "POST", body: JSON.stringify(body) }),
  configHistory: (guildId: string) => request<{ imports: any[] }>(`/guilds/${guildId}/config-transfer/history`),
  getRoleAutomation: (guildId: string) => request<{ join: any; rules: any[]; bot_position?: number }>(`/guilds/${guildId}/autorole/v2`),
  saveJoinRoles: (guildId: string, data: any) => request<any>(`/guilds/${guildId}/autorole/v2/join`, { method: "PUT", body: JSON.stringify(data) }),
  createRoleRule: (guildId: string, data: any) => request<any>(`/guilds/${guildId}/autorole/v2/rules`, { method: "POST", body: JSON.stringify(data) }),
  updateRoleRule: (guildId: string, ruleId: string, data: any) => request<any>(`/guilds/${guildId}/autorole/v2/rules/${ruleId}`, { method: "PATCH", body: JSON.stringify(data) }),
  duplicateRoleRule: (guildId: string, ruleId: string) => request<any>(`/guilds/${guildId}/autorole/v2/rules/${ruleId}/duplicate`, { method: "POST" }),
  deleteRoleRule: (guildId: string, ruleId: string) => request<any>(`/guilds/${guildId}/autorole/v2/rules/${ruleId}`, { method: "DELETE" }),
  getAutoRole: (guildId: string) => request<AutoRoleConfig>(`/guilds/${guildId}/autorole`),
  updateAutoRole: (guildId: string, data: AutoRoleUpdate) =>
    request<{ status: string }>(`/guilds/${guildId}/autorole`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getTracking: (guildId: string) => request<any>(`/guilds/${guildId}/tracking`),
  updateTracking: (guildId: string, data: any) =>
    request<{ status: string }>(`/guilds/${guildId}/tracking`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getJ2C: (guildId: string) => request<any>(`/guilds/${guildId}/j2c`),
  updateJ2C: (guildId: string, data: any) =>
    request<{ status: string }>(`/guilds/${guildId}/j2c`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getJoinDM: (guildId: string) => request<any>(`/guilds/${guildId}/joindm`),
  updateJoinDM: (guildId: string, data: any) =>
    request<{ status: string }>(`/guilds/${guildId}/joindm`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getCustomRoles: (guildId: string) => request<any>(`/guilds/${guildId}/customroles`),
  updateCustomRoles: (guildId: string, data: any) =>
    request<{ status: string }>(`/guilds/${guildId}/customroles`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getAutoReactRules: (guildId: string) => request<{ rules: any[] }>(`/guilds/${guildId}/autoreact/v2`),
  createAutoReactRule: (guildId: string, data: any) => request<any>(`/guilds/${guildId}/autoreact/v2`, { method: "POST", body: JSON.stringify(data) }),
  updateAutoReactRule: (guildId: string, ruleId: string, data: any) =>
    request<any>(`/guilds/${guildId}/autoreact/v2/${ruleId}`, { method: "PATCH", body: JSON.stringify(data) }),
  duplicateAutoReactRule: (guildId: string, ruleId: string) =>
    request<any>(`/guilds/${guildId}/autoreact/v2/${ruleId}/duplicate`, { method: "POST" }),
  deleteAutoReactRule: (guildId: string, ruleId: string) =>
    request<any>(`/guilds/${guildId}/autoreact/v2/${ruleId}`, { method: "DELETE" }),
  getAutoReact: (guildId: string) => request<any>(`/guilds/${guildId}/autoreact`),
  updateAutoReact: (guildId: string, data: any) =>
    request<{ status: string }>(`/guilds/${guildId}/autoreact`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getInvcRole: (guildId: string) => request<any>(`/guilds/${guildId}/invcrole`),
  updateInvcRole: (guildId: string, data: any) =>
    request<{ status: string }>(`/guilds/${guildId}/invcrole`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getRoleMenus: (guildId: string) => request<{ menus: any[]; bot_position?: number }>(`/guilds/${guildId}/reactionroles/v2`),
  getRoleMenu: (guildId: string, menuId: string) => request<any>(`/guilds/${guildId}/reactionroles/v2/${menuId}`),
  createRoleMenu: (guildId: string, data: any) => request<any>(`/guilds/${guildId}/reactionroles/v2`, { method: "POST", body: JSON.stringify(data) }),
  updateRoleMenu: (guildId: string, menuId: string, data: any) => request<any>(`/guilds/${guildId}/reactionroles/v2/${menuId}`, { method: "PATCH", body: JSON.stringify(data) }),
  duplicateRoleMenu: (guildId: string, menuId: string) => request<any>(`/guilds/${guildId}/reactionroles/v2/${menuId}/duplicate`, { method: "POST" }),
  deleteRoleMenu: (guildId: string, menuId: string, removeReactions = false) => request<any>(`/guilds/${guildId}/reactionroles/v2/${menuId}?remove_reactions=${removeReactions ? "true" : "false"}`, { method: "DELETE" }),
  publishRoleMenu: (guildId: string, menuId: string, data: any) => request<any>(`/guilds/${guildId}/reactionroles/v2/${menuId}/publish`, { method: "POST", body: JSON.stringify(data) }),
  republishRoleMenu: (guildId: string, menuId: string) => request<any>(`/guilds/${guildId}/reactionroles/v2/${menuId}/republish`, { method: "POST" }),
  getRoleMenuMessages: (guildId: string, channelId: string, link = "") => request<{ messages: any[] }>(`/guilds/${guildId}/reactionroles/v2/messages?channel_id=${encodeURIComponent(channelId)}&link=${encodeURIComponent(link)}`),
  getRR: (guildId: string) => request<any>(`/guilds/${guildId}/reactionroles`),
  updateRR: (guildId: string, data: any) =>
    request<{ status: string }>(`/guilds/${guildId}/reactionroles`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getInvites: (guildId: string) => request<any>(`/guilds/${guildId}/invites`),
  getInvitesV2: (guildId: string) => request<any>(`/guilds/${guildId}/invites/v2`),
  getInviteMember: (guildId: string, userId: string) => request<any>(`/guilds/${guildId}/invites/v2/members/${userId}`),
  saveInviteSettings: (guildId: string, data: { log_channel_id: string | null }) =>
    request<any>(`/guilds/${guildId}/invites/v2/settings`, { method: "PUT", body: JSON.stringify(data) }),
  getGiveaways: (guildId: string) => request<any>(`/guilds/${guildId}/giveaways`),
  createGiveaway: (guildId: string, data: Record<string, unknown>) =>
    request<any>(`/guilds/${guildId}/giveaways`, { method: "POST", body: JSON.stringify(data) }),
  updateGiveaway: (guildId: string, giveawayId: string, data: Record<string, unknown>) =>
    request<any>(`/guilds/${guildId}/giveaways/${giveawayId}`, { method: "PATCH", body: JSON.stringify(data) }),
  endGiveaway: (guildId: string, giveawayId: string) =>
    request<any>(`/guilds/${guildId}/giveaways/${giveawayId}/end`, { method: "POST" }),
  rerollGiveaway: (guildId: string, giveawayId: string) =>
    request<any>(`/guilds/${guildId}/giveaways/${giveawayId}/reroll`, { method: "POST" }),
  archiveGiveaway: (guildId: string, giveawayId: string) =>
    request<any>(`/guilds/${guildId}/giveaways/${giveawayId}`, { method: "DELETE" }),
  updateInvites: (guildId: string, data: any) =>
    request<{ status: string }>(`/guilds/${guildId}/invites`, {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  getAdminStats: () => request<AdminStats>("/admin/stats"),
  getAdminConfig: () => request<AdminConfig>("/admin/config"),
  updateAdminConfig: (data: AdminConfigUpdate) =>
    request<{ status: string }>("/admin/config", {
      method: "PATCH",
      body: JSON.stringify(data),
    }),

  listAccessGrants: (guildId?: string) =>
    request<unknown[]>(`/access/grants${guildId ? `?guild_id=${guildId}` : ""}`),
  createAccessGrant: (data: any) =>
    request<{ id: string }>("/access/grants", {
      method: "POST",
      body: JSON.stringify(data),
    }),
  listMessageTemplates: (guildId: string) =>
    request<{ templates: any[] }>(`/guilds/${guildId}/messages/templates`),
  createMessageTemplate: (guildId: string, data: { name: string; payload: unknown }) =>
    request<any>(`/guilds/${guildId}/messages/templates`, { method: "POST", body: JSON.stringify(data) }),
  updateMessageTemplate: (guildId: string, templateId: string, data: { name?: string; payload?: unknown }) =>
    request<any>(`/guilds/${guildId}/messages/templates/${templateId}`, { method: "PATCH", body: JSON.stringify(data) }),
  deleteMessageTemplate: (guildId: string, templateId: string) =>
    request<{ status: string }>(`/guilds/${guildId}/messages/templates/${templateId}`, { method: "DELETE" }),
  messageContext: (guildId: string) =>
    request<{ variables: { id: string; value: string }[] }>(`/guilds/${guildId}/messages/context`),
  listGuildEmojis: (guildId: string) =>
    request<{ emojis: { id: string; name: string; url: string; animated: boolean }[] }>(`/guilds/${guildId}/emojis`),
  uploadMessageMedia: (guildId: string, body: FormData) =>
    request<{ key: string }>(`/guilds/${guildId}/media`, { method: "POST", body }),
  sendGuildMessage: (guildId: string, data: { channel_id: string; template_id?: string | null; payload: unknown }) =>
    request<any>(`/guilds/${guildId}/messages/send`, { method: "POST", body: JSON.stringify(data) }),
  listSentMessages: (guildId: string) => request<{ sent: any[] }>(`/guilds/${guildId}/messages/sent`),
  editSentMessage: (guildId: string, sentId: string, payload: unknown) =>
    request<any>(`/guilds/${guildId}/messages/sent/${sentId}`, { method: "PATCH", body: JSON.stringify({ payload }) }),
  resendSentMessage: (guildId: string, sentId: string) =>
    request<any>(`/guilds/${guildId}/messages/sent/${sentId}/resend`, { method: "POST" }),
  removeSentMessage: (guildId: string, sentId: string) =>
    request<any>(`/guilds/${guildId}/messages/sent/${sentId}/remove`, { method: "POST" }),
  deleteSentRecord: (guildId: string, sentId: string) =>
    request<{ status: string }>(`/guilds/${guildId}/messages/sent/${sentId}`, { method: "DELETE" }),

  revokeAccessGrant: (grantId: string) =>
    request<{ revoked: boolean }>(`/access/grants/${grantId}`, { method: "DELETE" }),
  listAccessRoles: () => request<unknown[]>("/access/roles"),
  createCustomAccessRole: (data: any) =>
    request<{ id: string }>("/access/roles/custom", {
      method: "POST",
      body: JSON.stringify(data),
    }),
};

export { ApiError };
