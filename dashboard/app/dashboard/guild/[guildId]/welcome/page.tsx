import React from "react";
import { WelcomeWorkspace } from "@/components/dashboard/welcome-workspace";
import { api } from "@/lib/api";

export default async function WelcomePage({
  params,
  searchParams,
}: {
  params: { guildId: string };
  searchParams?: { tab?: string };
}) {
  const [home, emojis] = await Promise.all([
    api.getWelcomeHome(params.guildId).catch(() => null),
    api.listGuildEmojis(params.guildId).catch(() => ({ emojis: [] })),
  ]);
  const tab = searchParams?.tab === "dm" || searchParams?.tab === "goodbye" ? searchParams.tab : "welcome";

  return <WelcomeWorkspace guildId={params.guildId} home={home} emojis={emojis.emojis || []} initialMode={tab} />;
}
