import React from "react";
import { CommandsWorkspace } from "@/components/dashboard/commands-workspace";
import { api } from "@/lib/api";

export default async function CommandsPage({ params }: { params: { guildId: string } }) {
  const [home, channels, roles] = await Promise.all([
    api
      .getCommands(params.guildId, "?page=1&page_size=25")
      .then((value) => ({ value, failed: false }))
      .catch(() => ({ value: null, failed: true })),
    api.getChannels(params.guildId).catch(() => []),
    api.getRoles(params.guildId).catch(() => []),
  ]);
  return (
    <CommandsWorkspace
      guildId={params.guildId}
      initial={home.value}
      initialError={home.failed ? "Commands could not be loaded" : null}
      channels={Array.isArray(channels) ? channels : []}
      roles={Array.isArray(roles) ? roles : []}
    />
  );
}
