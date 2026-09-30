import React from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/dashboard/page-header";

const TicketsForm = dynamic(() => import("@/components/dashboard/tickets-form").then((mod) => mod.TicketsForm), {
  loading: () => <div className="h-24 w-full animate-pulse rounded-md bg-surface-2" />,
});

export default async function TicketsPage({ params }: { params: { guildId: string } }) {
  const config = await api.getTickets(params.guildId);
  if (!config) return null;

  return (
    <div className="space-y-6">
      <PageHeader
        title="Tickets"
        description="Configure support categories, channels, and staff roles for this server."
      />
      <TicketsForm initialConfig={config} guildId={params.guildId} />
    </div>
  );
}
