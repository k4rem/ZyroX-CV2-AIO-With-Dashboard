import React from "react";
import { LoggingV2Workspace } from "@/components/dashboard/logging-v2-workspace";
import { api } from "@/lib/api";

const EMPTY = {
  overview: { total: 0, by_category: {}, top_types: [], series: [], heatmap: null },
  routes: [],
  events: [],
  next_cursor: null,
};

export default async function LoggingPage({ params }: { params: { guildId: string } }) {
  const [home, channels] = await Promise.all([
    api.getLoggingV2(params.guildId).catch(() => null),
    api.getChannels(params.guildId).catch(() => []),
  ]);
  return <LoggingV2Workspace guildId={params.guildId} initial={home ?? EMPTY} channels={channels ?? []} />;
}
