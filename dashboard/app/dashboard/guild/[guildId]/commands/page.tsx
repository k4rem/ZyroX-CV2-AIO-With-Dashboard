import React from "react";
import { CommandManager } from "@/components/dashboard/command-manager";
import { api } from "@/lib/api";

export default async function CommandsPage({ params }: { params: { guildId: string } }) {
  const body = await api.getCommands(params.guildId).catch(() => null);
  return <CommandManager guildId={params.guildId} initial={body?.commands ?? []} />;
}
