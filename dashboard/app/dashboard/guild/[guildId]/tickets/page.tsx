import React from "react";
import { TicketsWorkspace } from "@/components/dashboard/tickets-workspace";
import { api } from "@/lib/api";

export default async function TicketsPage({ params }: { params: { guildId: string } }) {
  const [config, channels, roles, bot] = await Promise.all([
    api.getTickets(params.guildId),
    api.getChannels(params.guildId).catch(() => []),
    api.getRoles(params.guildId).catch(() => []),
    api.getBotStatus().catch(() => null),
  ]);
  if (!config) return null;

  return (
    <TicketsWorkspace
      guildId={params.guildId}
      initialConfig={config}
      channels={channels ?? []}
      roles={roles ?? []}
      botName={bot?.user ?? "Bot"}
      botAvatar={bot?.avatar_url ?? null}
    />
  );
}
