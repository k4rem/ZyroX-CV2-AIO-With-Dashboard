import React from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/dashboard/page-header";

const WelcomeForm = dynamic(() => import("@/components/dashboard/welcome-form").then((mod) => mod.WelcomeForm), {
  loading: () => <div className="h-24 w-full animate-pulse rounded-md bg-surface-2" />,
});

export default async function WelcomePage({ params }: { params: { guildId: string } }) {
  const [welcomeData, channelsData] = await Promise.all([
    api.getWelcome(params.guildId),
    api.getChannels(params.guildId),
  ]);

  if (!welcomeData) return null;

  return (
    <div className="space-y-6">
      <PageHeader title="Welcome" description="Configure join messages and channels for new members." />
      <WelcomeForm initialConfig={welcomeData} channels={channelsData} guildId={params.guildId} />
    </div>
  );
}
