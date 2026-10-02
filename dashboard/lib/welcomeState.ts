import { emptyEmbed, emptyMessage, type EmbedDraft, type MediaRef, type MessageDraft, type MessageVariable } from "./messagePayload";

export const WELCOME_MESSAGE_VARIABLES: MessageVariable[] = [
  { id: "user", label: "Mention", description: "Mentions the member", example: "@member" },
  { id: "user_avatar", label: "Avatar", description: "The member's avatar URL", example: "https://cdn.discordapp.com/avatars/…" },
  { id: "user_name", label: "Username", description: "The member's username", example: "aero" },
  { id: "user_id", label: "User ID", description: "The member's ID", example: "567817806889091084" },
  { id: "user_nick", label: "Nickname", description: "The member's display name", example: "Aero" },
  { id: "user_joindate", label: "Join date", description: "When they joined this server", example: "Thu, Oct 01, 2026" },
  { id: "user_createdate", label: "Account created", description: "When their Discord account was created", example: "Mon, Jan 01, 2024" },
  { id: "server_name", label: "Server name", description: "This server's name", example: "CLS" },
  { id: "server_id", label: "Server ID", description: "This server's ID", example: "1543105121804615781" },
  { id: "server_membercount", label: "Member count", description: "How many members are in the server", example: "128" },
  { id: "server_icon", label: "Server icon", description: "This server's icon URL", example: "https://cdn.discordapp.com/icons/…" },
  { id: "timestamp", label: "Timestamp", description: "The time the message is sent", example: "Today at 8:00 PM" },
];

export const GOODBYE_MESSAGE_VARIABLES = WELCOME_MESSAGE_VARIABLES.filter((item) => item.id !== "user");

function media(value: unknown): MediaRef {
  if (!value || typeof value !== "object") return null;
  const kind = (value as { kind?: unknown }).kind;
  const raw = (value as { value?: unknown }).value;
  if ((kind === "url" || kind === "media") && typeof raw === "string") return { kind, value: raw };
  return null;
}

function asEmbed(value: unknown): EmbedDraft {
  const base = emptyEmbed();
  const embed = (value && typeof value === "object" ? value : {}) as Record<string, unknown>;
  const author = (embed.author && typeof embed.author === "object" ? embed.author : {}) as Record<string, unknown>;
  const footer = (embed.footer && typeof embed.footer === "object" ? embed.footer : {}) as Record<string, unknown>;
  const fields = Array.isArray(embed.fields) ? embed.fields : [];
  return {
    ...base,
    title: typeof embed.title === "string" ? embed.title : "",
    url: typeof embed.url === "string" ? embed.url : "",
    description: typeof embed.description === "string" ? embed.description : "",
    color: typeof embed.color === "string" && embed.color ? embed.color : base.color,
    author: {
      name: typeof author.name === "string" ? author.name : "",
      url: typeof author.url === "string" ? author.url : "",
      icon: media(author.icon),
    },
    thumbnail: media(embed.thumbnail),
    image: media(embed.image),
    fields: fields.map((field) => {
      const row = (field && typeof field === "object" ? field : {}) as Record<string, unknown>;
      return {
        name: typeof row.name === "string" ? row.name : "",
        value: typeof row.value === "string" ? row.value : "",
        inline: Boolean(row.inline),
      };
    }),
    footer: {
      text: typeof footer.text === "string" ? footer.text : "",
      icon: media(footer.icon),
    },
    timestamp: Boolean(embed.timestamp),
  };
}

export function asMessageDraft(raw: unknown): MessageDraft {
  if (!raw || typeof raw !== "object") return emptyMessage();
  const record = raw as Record<string, unknown>;
  const embeds = Array.isArray(record.embeds) ? record.embeds.map(asEmbed) : [emptyEmbed()];
  const buttons = Array.isArray(record.buttons)
    ? record.buttons.map((item) => {
        const button = (item && typeof item === "object" ? item : {}) as Record<string, unknown>;
        return {
          label: typeof button.label === "string" ? button.label : "",
          url: typeof button.url === "string" ? button.url : "",
          emoji: typeof button.emoji === "string" ? button.emoji : "",
        };
      })
    : [];
  return {
    content: typeof record.content === "string" ? record.content : "",
    embeds: embeds.length ? embeds : [emptyEmbed()],
    buttons,
  };
}

export function sameWelcomeState(left: unknown, right: unknown): boolean {
  return JSON.stringify(left) === JSON.stringify(right);
}
