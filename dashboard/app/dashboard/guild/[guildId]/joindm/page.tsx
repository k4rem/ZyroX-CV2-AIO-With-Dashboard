import React from "react";
import { JoinDmWorkspace } from "@/components/dashboard/joindm-workspace";
import { api } from "@/lib/api";

export default async function JoinDMPage({ params }: { params: { guildId: string } }) {
  const [config, guild, bot] = await Promise.all([
    api.getJoinDM(params.guildId),
    api.getGuildDetails(params.guildId).catch(() => null),
    api.getBotStatus().catch(() => null),
  ]);

  return (
    <JoinDmWorkspace
      guildId={params.guildId}
      initialMessage={typeof config?.message === "string" ? config.message : ""}
      guildName={guild?.name ?? null}
      botName={bot?.user ?? "Bot"}
      botAvatar={bot?.avatar_url ?? null}
    />
  );
}
