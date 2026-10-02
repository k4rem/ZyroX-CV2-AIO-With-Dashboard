import React from "react";
import { WelcomeWorkspace } from "@/components/dashboard/welcome-workspace";
import { LoadError } from "@/components/platform/load-error";
import { api } from "@/lib/api";

export default async function WelcomePage({
  params,
  searchParams,
}: {
  params: { guildId: string };
  searchParams?: { tab?: string };
}) {
  let home;
  try {
    home = await api.getWelcomeHome(params.guildId);
  } catch (error) {
    return <LoadError title="Welcome could not be loaded" error={error} />;
  }
  const emojis = await api.listGuildEmojis(params.guildId).catch(() => ({ emojis: [] }));
  const tab = searchParams?.tab === "dm" || searchParams?.tab === "goodbye" ? searchParams.tab : "welcome";

  return <WelcomeWorkspace guildId={params.guildId} home={home} emojis={emojis.emojis || []} initialMode={tab} />;
}
