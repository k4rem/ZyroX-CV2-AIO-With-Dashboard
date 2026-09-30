import React from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/dashboard/page-header";

const AutomodForm = dynamic(() => import("@/components/dashboard/automod-form").then((mod) => mod.AutomodForm), {
  loading: () => <div className="h-24 w-full animate-pulse rounded-md bg-surface-2" />,
});

export default async function AutomodPage({ params }: { params: { guildId: string } }) {
  const config = await api.getAutomod(params.guildId);
  if (!config) return null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Automod"
        description="Configure rule-based message filters and punishments for this server."
      />
      <AutomodForm initialConfig={config} guildId={params.guildId} />
    </div>
  );
}
