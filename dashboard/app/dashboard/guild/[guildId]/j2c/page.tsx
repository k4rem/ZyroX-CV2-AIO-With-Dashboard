import React from "react";
import { J2CWorkspace } from "@/components/dashboard/j2c-workspace";
import { api } from "@/lib/api";

export const revalidate = 0;

export default async function J2CPage({ params }: { params: { guildId: string } }) {
  const [config, channels] = await Promise.all([api.getJ2C(params.guildId), api.getChannels(params.guildId)]);
  if (!config) return null;
  return <J2CWorkspace guildId={params.guildId} initialConfig={config} channels={channels ?? []} />;
}
