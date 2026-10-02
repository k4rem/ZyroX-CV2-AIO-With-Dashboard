import React from "react";
import { AutomodWorkspace } from "@/components/dashboard/automod-workspace";
import { LoadError } from "@/components/platform/load-error";
import { api } from "@/lib/api";

export async function AutomodPage({ guildId, tab }: { guildId: string; tab: "overview" | "rules" | "violations" | "strikes" | "settings" }) {
  try {
    const [config, channels, roles, runtime] = await Promise.all([
      api.getAutomodV2(guildId),
      api.getChannels(guildId).catch(() => []),
      api.getRoles(guildId).catch(() => []),
      api.getRuntimeHealth(guildId).catch(() => null),
    ]);
    return <AutomodWorkspace guildId={guildId} tab={tab} config={config} channels={channels} roles={roles} runtime={runtime} />;
  } catch (error) {
    return <LoadError title="Automod could not be loaded" error={error} />;
  }
}
