/**
 * Welcome message formatting shared by the composer and the Discord preview.
 * Tokens and colour rules match bot/cogs/events/greet2.py — nothing is added
 * that the bot does not substitute.
 */

/** greet2 falls back to 0x2F3136 when colour is missing, not a string, or has no leading #. */
export const BOT_DEFAULT_EMBED_COLOR = "#2F3136";

export const WELCOME_COLOR_ERROR =
  "Use a # colour, e.g. #6025E2 — Discord will otherwise use the default grey";

/** The 12 placeholders greet2 actually substitutes. The phase doc says 13; the bot has these. */
export const WELCOME_VARIABLES = [
  { key: "user", label: "Mention", hint: "Mentions the member" },
  { key: "user_avatar", label: "Avatar URL", hint: "The member's avatar" },
  { key: "user_name", label: "Username", hint: "The member's username" },
  { key: "user_id", label: "User ID", hint: "The member's ID" },
  { key: "user_nick", label: "Nickname", hint: "The member's display name" },
  { key: "user_joindate", label: "Join date", hint: "When they joined this server" },
  { key: "user_createdate", label: "Account created", hint: "When their Discord account was created" },
  { key: "server_name", label: "Server name", hint: "This server's name" },
  { key: "server_id", label: "Server ID", hint: "This server's ID" },
  { key: "server_membercount", label: "Member count", hint: "How many members are in the server" },
  { key: "server_icon", label: "Server icon", hint: "This server's icon URL" },
  { key: "timestamp", label: "Timestamp", hint: "The time the message is sent" },
] as const;

export type WelcomeVarKey = (typeof WELCOME_VARIABLES)[number]["key"];

const WELCOME_KEYS = new Set<string>(WELCOME_VARIABLES.map((v) => v.key));

export interface WelcomePreviewContext {
  userId: string | null;
  userName: string | null;
  userAvatar: string | null;
  userNick: string | null;
  userJoinDate: string | null;
  userCreateDate: string | null;
  serverName: string | null;
  serverId: string | null;
  serverMemberCount: number | null;
  serverIcon: string | null;
  timestamp: string | null;
}

export interface WelcomeEmbedDraft {
  message: string;
  title: string;
  description: string;
  color: string;
  footer_text: string;
  footer_icon: string;
  author_name: string;
  author_icon: string;
  thumbnail: string;
  image: string;
}

export interface WelcomeDraft {
  welcome_type: "simple" | "embed";
  welcome_message: string;
  channel_id: string | null;
  auto_delete_duration: number | null;
  embed: WelcomeEmbedDraft;
}

export function emptyEmbed(): WelcomeEmbedDraft {
  return {
    message: "",
    title: "",
    description: "",
    color: "",
    footer_text: "",
    footer_icon: "",
    author_name: "",
    author_icon: "",
    thumbnail: "",
    image: "",
  };
}

/** CLS default. Colour always includes # so greet2 does not ignore it. */
export function defaultWelcomeEmbed(): WelcomeEmbedDraft {
  return {
    message: "",
    title: "Welcome to {server_name}!",
    description: "Hi {user}, we're glad you joined! You are member #{server_membercount}.",
    color: "#2F3136",
    footer_text: "",
    footer_icon: "",
    author_name: "",
    author_icon: "",
    thumbnail: "{user_avatar}",
    image: "",
  };
}

export function welcomeValueMap(ctx: WelcomePreviewContext): Record<string, string | null> {
  return {
    user: ctx.userId ? `<@${ctx.userId}>` : null,
    user_avatar: ctx.userAvatar,
    user_name: ctx.userName,
    user_id: ctx.userId,
    user_nick: ctx.userNick,
    user_joindate: ctx.userJoinDate,
    user_createdate: ctx.userCreateDate,
    server_name: ctx.serverName,
    server_id: ctx.serverId,
    server_membercount: ctx.serverMemberCount == null ? null : String(ctx.serverMemberCount),
    server_icon: ctx.serverIcon,
    timestamp: ctx.timestamp,
  };
}

export function substituteWelcome(text: string, values: Record<string, string | null>) {
  const unknown: string[] = [];
  const unresolved: string[] = [];
  const resolved = (text ?? "").replace(/\{(\w+)\}/g, (full, raw: string) => {
    const key = raw.toLowerCase();
    if (!WELCOME_KEYS.has(key)) {
      if (!unknown.includes(raw)) unknown.push(raw);
      return full;
    }
    const value = values[key];
    if (value == null || value === "") {
      if (!unresolved.includes(key)) unresolved.push(key);
      return full;
    }
    return value;
  });
  return { text: resolved, unknown, unresolved };
}

export function interpretWelcomeColor(raw: string): {
  valid: boolean;
  preview: string;
  stored: string | null;
  error: string | null;
} {
  const value = (raw ?? "").trim();
  if (!value) {
    return { valid: true, preview: BOT_DEFAULT_EMBED_COLOR, stored: null, error: null };
  }
  if (/^#[0-9A-Fa-f]{6}$/.test(value)) {
    const stored = `#${value.slice(1).toUpperCase()}`;
    return { valid: true, preview: stored, stored, error: null };
  }
  return { valid: false, preview: BOT_DEFAULT_EMBED_COLOR, stored: null, error: WELCOME_COLOR_ERROR };
}

export function safeHttpUrl(value: string | null | undefined): string | null {
  if (!value) return null;
  try {
    const url = new URL(value);
    if (url.protocol === "https:" || url.protocol === "http:") return url.toString();
  } catch {
    return null;
  }
  return null;
}

function textField(value: unknown): string {
  return typeof value === "string" ? value : "";
}

export function welcomeDraftFromApi(config: {
  welcome_type?: string | null;
  welcome_message?: string | null;
  channel_id?: string | number | null;
  auto_delete_duration?: number | null;
  embed_data?: Partial<WelcomeEmbedDraft> | null;
}): WelcomeDraft {
  const embed = config.embed_data ?? {};
  const channel = config.channel_id == null || config.channel_id === "" ? null : String(config.channel_id);
  const duration =
    typeof config.auto_delete_duration === "number" && config.auto_delete_duration > 0
      ? config.auto_delete_duration
      : null;
  return {
    welcome_type: config.welcome_type === "embed" ? "embed" : "simple",
    welcome_message: textField(config.welcome_message),
    channel_id: channel,
    auto_delete_duration: duration,
    embed: {
      message: textField(embed.message),
      title: textField(embed.title),
      description: textField(embed.description),
      color: textField(embed.color),
      footer_text: textField(embed.footer_text),
      footer_icon: textField(embed.footer_icon),
      author_name: textField(embed.author_name),
      author_icon: textField(embed.author_icon),
      thumbnail: textField(embed.thumbnail),
      image: textField(embed.image),
    },
  };
}

/** Payload the welcome form saves. Invalid colours must be rejected by the caller. */
export function welcomeUpdatePayload(draft: WelcomeDraft) {
  const color = interpretWelcomeColor(draft.embed.color);
  return {
    welcome_type: draft.welcome_type,
    welcome_message: draft.welcome_message,
    channel_id: draft.channel_id,
    auto_delete_duration: draft.auto_delete_duration ?? 0,
    embed_data: {
      message: draft.embed.message || null,
      title: draft.embed.title || null,
      description: draft.embed.description || null,
      color: color.stored,
      footer_text: draft.embed.footer_text || null,
      footer_icon: draft.embed.footer_icon || null,
      author_name: draft.embed.author_name || null,
      author_icon: draft.embed.author_icon || null,
      thumbnail: draft.embed.thumbnail || null,
      image: draft.embed.image || null,
    },
  };
}

export function previewClock(now = new Date()): string {
  const hh = String(now.getHours()).padStart(2, "0");
  const mm = String(now.getMinutes()).padStart(2, "0");
  return `${hh}:${mm}`;
}
