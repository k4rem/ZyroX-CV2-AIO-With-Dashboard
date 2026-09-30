import React from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/dashboard/page-header";

const LoggingForm = dynamic(() => import("@/components/dashboard/logging-form").then((mod) => mod.LoggingForm), {
  loading: () => <div className="h-24 w-full animate-pulse rounded-md bg-surface-2" />,
});

export default async function LoggingPage({ params }: { params: { guildId: string } }) {
  const [loggingData, channelsData] = await Promise.all([
    api.getLogging(params.guildId),
    api.getChannels(params.guildId),
  ]);

  if (!loggingData) return null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Logging"
        description="Choose which events are logged and which channels receive them."
      />
      <LoggingForm initialConfig={loggingData} channels={channelsData} guildId={params.guildId} />
    </div>
  );
}
