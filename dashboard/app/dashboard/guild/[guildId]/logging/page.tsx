import React from "react";
import { LoggingV2Workspace } from "@/components/dashboard/logging-v2-workspace";
import { api } from "@/lib/api";

const EMPTY = {
  overview: { total: 0, by_category: {}, top_types: [], series: [], heatmap: null },
  routes: [],
  events: [],
  next_cursor: null,
  event_types: [],
  retention: { events_days: 90, message_content_days: 30 },
  ignores: { channels: [], roles: [], users: [] },
};

export default async function LoggingPage({ params }: { params: { guildId: string } }) {
  const [home, channels, roles] = await Promise.all([
    api.getLoggingV2(params.guildId).catch(() => null),
    api.getChannels(params.guildId).catch(() => []),
    api.getRoles(params.guildId).catch(() => []),
  ]);
  return (
    <LoggingV2Workspace
      guildId={params.guildId}
      initial={home ?? EMPTY}
      channels={Array.isArray(channels) ? channels : []}
      roles={Array.isArray(roles) ? roles : []}
    />
  );
}
