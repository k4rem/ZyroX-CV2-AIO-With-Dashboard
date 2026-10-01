import React from "react";
import { getServerSession } from "next-auth";
import { WelcomeWorkspace } from "@/components/dashboard/welcome-workspace";
import { api } from "@/lib/api";
import { authOptions } from "@/lib/auth";

export default async function WelcomePage({ params }: { params: { guildId: string } }) {
  const session = await getServerSession(authOptions);
  const [welcomeData, channelsData, guild, bot] = await Promise.all([
    api.getWelcome(params.guildId),
    api.getChannels(params.guildId),
    api.getGuildDetails(params.guildId).catch(() => null),
    api.getBotStatus().catch(() => null),
  ]);

  if (!welcomeData) return null;

  return (
    <WelcomeWorkspace
      guildId={params.guildId}
      initialConfig={welcomeData}
      channels={channelsData ?? []}
      guildName={guild?.name ?? null}
      guildIcon={guild?.icon ?? null}
      memberCount={typeof guild?.member_count === "number" ? guild.member_count : null}
      serverId={guild?.id != null ? String(guild.id) : params.guildId}
      botName={bot?.user ?? "Bot"}
      botAvatar={bot?.avatar_url ?? null}
      viewer={{
        id: session?.user?.id ?? null,
        name: session?.user?.name ?? null,
        image: session?.user?.image ?? null,
      }}
    />
  );
}
