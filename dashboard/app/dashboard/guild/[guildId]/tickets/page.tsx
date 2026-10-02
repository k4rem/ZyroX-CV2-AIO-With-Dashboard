import React from "react";
import { TicketsV2Workspace } from "@/components/dashboard/tickets-v2-workspace";
import { api } from "@/lib/api";

export default async function TicketsPage({ params }: { params: { guildId: string } }) {
  const [workspace, channels, roles] = await Promise.all([
    api.getTicketsV2(params.guildId).catch(() => null),
    api.getChannels(params.guildId).catch(() => []),
    api.getRoles(params.guildId).catch(() => []),
  ]);
  const list = channels ?? [];
  const categories = list.filter((channel: { type?: string }) => channel.type === "4" || channel.type === "category");
  const text = list.filter((channel: { type?: string }) => ["0", "5", "text", "news"].includes(String(channel.type)));
  return (
    <TicketsV2Workspace
      guildId={params.guildId}
      initial={
        workspace ?? { open_now: 0, opened: 0, closed: 0, cooldown_seconds: 60, max_open: 1, blacklist: [], categories: [], panels: [], tickets: [] }
      }
      categories={categories}
      roles={(roles ?? []).map((role: { id: string | number; name: string }) => ({ id: String(role.id), name: role.name }))}
      channels={text.map((channel: { id: string | number; name: string; type?: string; parent_id?: string | null }) => ({
        id: String(channel.id),
        name: channel.name,
        type: String(channel.type ?? "0"),
        parent_id: channel.parent_id ? String(channel.parent_id) : null,
      }))}
    />
  );
}
