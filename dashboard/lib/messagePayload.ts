export const LIMITS = {
  content: 2000,
  title: 256,
  description: 4096,
  fieldName: 256,
  fieldValue: 1024,
  footer: 2048,
  author: 256,
  url: 512,
  fields: 25,
  embeds: 10,
  embedTotal: 6000,
  buttons: 5,
  buttonLabel: 80,
} as const;

export type MediaRef = { kind: "url" | "media"; value: string } | null;

export type EmbedField = { name: string; value: string; inline: boolean };

export type EmbedDraft = {
  title: string;
  url: string;
  description: string;
  color: string;
  author: { name: string; url: string; icon: MediaRef };
  thumbnail: MediaRef;
  image: MediaRef;
  fields: EmbedField[];
  footer: { text: string; icon: MediaRef };
  timestamp: boolean;
};

export type ButtonDraft = { label: string; url: string; emoji: string };

export type MessageDraft = {
  content: string;
  embeds: EmbedDraft[];
  buttons: ButtonDraft[];
};

export type MessageVariable = {
  id: string;
  label: string;
  description: string;
  example: string;
};

export const STANDALONE_VARIABLES: MessageVariable[] = [
  { id: "server_name", label: "Server name", description: "This server's name", example: "CLS" },
  { id: "server_membercount", label: "Member count", description: "How many members are in the server", example: "128" },
  { id: "server_icon", label: "Server icon", description: "URL of the server icon", example: "https://cdn.discordapp.com/icons/…" },
  { id: "timestamp", label: "Timestamp", description: "The time the message is sent", example: "Today at 8:00 PM" },
];

const HTTP = /^https:\/\//i;
const MEDIA_KEY = /^[a-f0-9]{32}\.png$/;
const HEX = /^#[0-9a-fA-F]{6}$/;

export function emptyEmbed(): EmbedDraft {
  return {
    title: "",
    url: "",
    description: "",
    color: "#9474ff",
    author: { name: "", url: "", icon: null },
    thumbnail: null,
    image: null,
    fields: [],
    footer: { text: "", icon: null },
    timestamp: false,
  };
}

export function emptyMessage(): MessageDraft {
  return { content: "", embeds: [emptyEmbed()], buttons: [] };
}

export function embedChars(embed: EmbedDraft): number {
  const fields = embed.fields.reduce((sum, field) => sum + field.name.length + field.value.length, 0);
  return embed.title.length + embed.description.length + embed.author.name.length + embed.footer.text.length + fields;
}

export function messageChars(message: MessageDraft): number {
  return message.embeds.reduce((sum, embed) => sum + embedChars(embed), 0);
}

export function applyVariables(text: string, values: Record<string, string>): string {
  return text.replace(/\{([a-z_]+)\}/g, (token, id) => (id in values ? values[id] : token));
}

export function insertAt(value: string, start: number, end: number, token: string): { value: string; cursor: number } {
  const next = value.slice(0, start) + token + value.slice(end);
  return { value: next, cursor: start + token.length };
}

export function variableQuery(value: string, cursor: number): { start: number; query: string } | null {
  const before = value.slice(0, cursor);
  const open = before.lastIndexOf("{");
  if (open < 0) return null;
  const fragment = before.slice(open + 1);
  if (fragment.includes("}") || fragment.includes("\n") || fragment.includes(" ")) return null;
  return { start: open, query: fragment };
}

function mediaError(ref: MediaRef, label: string, errors: string[]) {
  if (!ref) return;
  if (ref.kind === "media") {
    if (!MEDIA_KEY.test(ref.value)) errors.push(`${label} upload is invalid`);
    return;
  }
  if (!HTTP.test(ref.value) || ref.value.length > LIMITS.url) errors.push(`${label} must be an https URL`);
}

export function validateMessage(message: MessageDraft): string[] {
  const errors: string[] = [];
  if (message.content.length > LIMITS.content) errors.push(`Message content is over ${LIMITS.content} characters`);
  if (message.embeds.length > LIMITS.embeds) errors.push(`A message can have at most ${LIMITS.embeds} embeds`);
  if (message.buttons.length > LIMITS.buttons) errors.push(`A message can have at most ${LIMITS.buttons} link buttons`);
  message.embeds.forEach((embed, index) => {
    const label = `Embed ${index + 1}`;
    if (embed.title.length > LIMITS.title) errors.push(`${label} title is over ${LIMITS.title} characters`);
    if (embed.description.length > LIMITS.description) errors.push(`${label} description is over ${LIMITS.description} characters`);
    if (embed.url && !HTTP.test(embed.url)) errors.push(`${label} URL must start with https://`);
    if (embed.color && !HEX.test(embed.color)) errors.push(`${label} color must be a hex color`);
    if (embed.author.name.length > LIMITS.author) errors.push(`${label} author is over ${LIMITS.author} characters`);
    if (embed.author.url && !HTTP.test(embed.author.url)) errors.push(`${label} author URL must start with https://`);
    if (embed.footer.text.length > LIMITS.footer) errors.push(`${label} footer is over ${LIMITS.footer} characters`);
    if (embed.fields.length > LIMITS.fields) errors.push(`${label} has more than ${LIMITS.fields} fields`);
    mediaError(embed.author.icon, `${label} author icon`, errors);
    mediaError(embed.thumbnail, `${label} thumbnail`, errors);
    mediaError(embed.image, `${label} image`, errors);
    mediaError(embed.footer.icon, `${label} footer icon`, errors);
    embed.fields.forEach((field, fieldIndex) => {
      if (!field.name.trim() || !field.value.trim()) errors.push(`${label} field ${fieldIndex + 1} needs a name and value`);
      if (field.name.length > LIMITS.fieldName) errors.push(`${label} field name is too long`);
      if (field.value.length > LIMITS.fieldValue) errors.push(`${label} field value is too long`);
    });
  });
  if (messageChars(message) > LIMITS.embedTotal) errors.push(`Embeds are over ${LIMITS.embedTotal} characters`);
  message.buttons.forEach((button, index) => {
    if (!button.label.trim() || button.label.length > LIMITS.buttonLabel) errors.push(`Button ${index + 1} needs a label`);
    if (!HTTP.test(button.url)) errors.push(`Button ${index + 1} needs an https URL`);
  });
  const hasBody =
    message.content.trim() ||
    message.buttons.length > 0 ||
    message.embeds.some((embed) => embedChars(embed) > 0 || embed.image || embed.thumbnail);
  if (!hasBody) errors.push("Add message content, an embed, or a link button");
  return errors;
}

function asText(value: unknown): string {
  return typeof value === "string" ? value : "";
}

function asMedia(value: unknown): MediaRef {
  if (!value || typeof value !== "object") return null;
  const kind = (value as { kind?: unknown }).kind;
  const raw = (value as { value?: unknown }).value;
  if ((kind === "url" || kind === "media") && typeof raw === "string") return { kind, value: raw };
  return null;
}

export function parseMessageJson(raw: string): { message: MessageDraft | null; errors: string[] } {
  let data: unknown;
  try {
    data = JSON.parse(raw);
  } catch {
    return { message: null, errors: ["That file is not valid JSON"] };
  }
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return { message: null, errors: ["Message JSON must be an object"] };
  }
  const record = data as Record<string, unknown>;
  const unknown = Object.keys(record).filter((key) => !["content", "embeds", "buttons"].includes(key));
  if (unknown.length) return { message: null, errors: [`Unknown fields: ${unknown.join(", ")}`] };
  const embedsIn = Array.isArray(record.embeds) ? record.embeds : [];
  const buttonsIn = Array.isArray(record.buttons) ? record.buttons : [];
  if (!Array.isArray(record.embeds) && record.embeds != null) return { message: null, errors: ["Embeds must be a list"] };
  if (!Array.isArray(record.buttons) && record.buttons != null) return { message: null, errors: ["Buttons must be a list"] };
  const embeds: EmbedDraft[] = embedsIn.map((item) => {
    const embed = (item && typeof item === "object" ? item : {}) as Record<string, unknown>;
    const author = (embed.author && typeof embed.author === "object" ? embed.author : {}) as Record<string, unknown>;
    const footer = (embed.footer && typeof embed.footer === "object" ? embed.footer : {}) as Record<string, unknown>;
    const fields = Array.isArray(embed.fields) ? embed.fields : [];
    return {
      title: asText(embed.title),
      url: asText(embed.url),
      description: asText(embed.description),
      color: asText(embed.color) || "#9474ff",
      author: { name: asText(author.name), url: asText(author.url), icon: asMedia(author.icon) },
      thumbnail: asMedia(embed.thumbnail),
      image: asMedia(embed.image),
      fields: fields.map((field) => {
        const row = (field && typeof field === "object" ? field : {}) as Record<string, unknown>;
        return { name: asText(row.name), value: asText(row.value), inline: Boolean(row.inline) };
      }),
      footer: { text: asText(footer.text), icon: asMedia(footer.icon) },
      timestamp: Boolean(embed.timestamp),
    };
  });
  const buttons: ButtonDraft[] = buttonsIn.map((item) => {
    const button = (item && typeof item === "object" ? item : {}) as Record<string, unknown>;
    return { label: asText(button.label), url: asText(button.url), emoji: asText(button.emoji) };
  });
  const message: MessageDraft = { content: asText(record.content), embeds, buttons };
  const errors = validateMessage(message);
  return { message: errors.length ? null : message, errors };
}

export function previewHint(message: MessageDraft): string {
  const title = message.embeds.find((embed) => embed.title.trim())?.title;
  const content = message.content.trim();
  return (title || content || "Empty message").slice(0, 80);
}

export function moveItem<T>(items: T[], index: number, direction: -1 | 1): T[] {
  const next = index + direction;
  if (next < 0 || next >= items.length) return items;
  const copy = items.slice();
  const [item] = copy.splice(index, 1);
  copy.splice(next, 0, item);
  return copy;
}
