import React from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/dashboard/page-header";

const AntiNukeForm = dynamic(() => import("@/components/dashboard/antinuke-form").then((mod) => mod.AntiNukeForm), {
  loading: () => <div className="h-24 w-full animate-pulse rounded-md bg-surface-2" />,
});

export default async function AntiNukePage({ params }: { params: { guildId: string } }) {
  const config = await api.getAntiNuke(params.guildId);
  if (!config) return null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Antinuke"
        description="Legacy protections against destructive admin actions; manage whitelist and master toggle."
      />
      <AntiNukeForm initialConfig={config} guildId={params.guildId} />
    </div>
  );
}
