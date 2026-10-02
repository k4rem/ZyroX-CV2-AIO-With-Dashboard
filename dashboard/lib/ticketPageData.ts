import { api } from "@/lib/api";

export async function ticketPageData(guildId: string) {
  const [workspace, channels, roles, emojis] = await Promise.all([
    api.getTicketsV2(guildId).catch(() => null),
    api.getChannels(guildId).catch(() => []),
    api.getRoles(guildId).catch(() => []),
    api.listGuildEmojis(guildId).catch(() => ({ emojis: [] })),
  ]);
  const list = channels ?? [];
  const roleOptions = (roles ?? []).map((role: { id: string | number; name: string }) => ({ id: String(role.id), name: role.name }));
  const discordCategories = list
    .filter((channel: { type?: string }) => channel.type === "4" || channel.type === "category")
    .map((channel: { id: string | number; name: string }) => ({ id: String(channel.id), name: channel.name }));
  const textChannels = list
    .filter((channel: { type?: string }) => ["0", "5", "text", "news"].includes(String(channel.type)))
    .map((channel: { id: string | number; name: string; type?: string; parent_id?: string | null }) => ({
      id: String(channel.id),
      name: channel.name,
      type: String(channel.type ?? "0"),
      parent_id: channel.parent_id ? String(channel.parent_id) : null,
    }));
  return {
    workspace: workspace ?? { categories: [], panels: [], cooldown_seconds: 60, max_open: 1, grace_minutes: 60, auto_close_hours: null, name_format: "ticket-{number}-{username}", transcript_channel_id: null },
    roleOptions,
    discordCategories,
    textChannels,
    emojis: emojis?.emojis ?? [],
    channelNames: Object.fromEntries(textChannels.map((channel) => [channel.id, channel.name])),
  };
}
