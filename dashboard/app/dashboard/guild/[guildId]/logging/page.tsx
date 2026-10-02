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

export default async function LoggingPage({
  params,
  searchParams,
}: {
  params: { guildId: string };
  searchParams?: { tab?: string };
}) {
  const [home, channels, roles] = await Promise.all([
    api.getLoggingV2(params.guildId, "?page=1&page_size=25").then((value) => ({ value, failed: false })).catch(() => ({ value: null, failed: true })),
    api.getChannels(params.guildId).catch(() => []),
    api.getRoles(params.guildId).catch(() => []),
  ]);
  return (
    <LoggingV2Workspace
      guildId={params.guildId}
      initial={home.value ?? EMPTY}
      initialError={home.failed ? "Logging could not be loaded" : null}
      channels={Array.isArray(channels) ? channels : []}
      roles={Array.isArray(roles) ? roles : []}
      initialTab={searchParams?.tab}
    />
  );
}
