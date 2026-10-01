import React from "react";
import { TicketsV2Workspace } from "@/components/dashboard/tickets-v2-workspace";
import { api } from "@/lib/api";

export default async function TicketsPage({ params }: { params: { guildId: string } }) {
  const [workspace, channels] = await Promise.all([
    api.getTicketsV2(params.guildId),
    api.getChannels(params.guildId).catch(() => []),
  ]);
  const categories = (channels ?? []).filter((channel: { type?: string }) => channel.type === "4");
  return (
    <TicketsV2Workspace
      guildId={params.guildId}
      initial={
        workspace ?? { open_now: 0, opened: 0, closed: 0, categories: [], panels: [], tickets: [] }
      }
      categories={categories}
    />
  );
}
