import React from "react";
import { api } from "@/lib/api";
import { SettingsForm } from "@/components/dashboard/settings-form";
import { PageHeader } from "@/components/dashboard/page-header";

export default async function GuildSettingsPage({ params }: { params: { guildId: string } }) {
  const config = await api.getPrefix(params.guildId);

  return (
    <div className="space-y-6">
      <PageHeader title="Bot settings" description="Core bot configuration for this server." />
      <SettingsForm initialPrefix={config.prefix} guildId={params.guildId} />
    </div>
  );
}
