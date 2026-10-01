import React from "react";
import dynamic from "next/dynamic";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/dashboard/page-header";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { isRootOwner } from "@/lib/utils";

const SecurityPanel = dynamic(
  () => import("@/components/dashboard/security-panel").then((mod) => mod.SecurityPanel),
  { loading: () => <div className="h-24 w-full animate-pulse rounded-md bg-surface-2" /> },
);

export default async function AntiNukePage({ params }: { params: { guildId: string } }) {
  const [summary, session] = await Promise.all([api.getSecurity(params.guildId), getServerSession(authOptions)]);
  const isRoot = isRootOwner(session?.user?.id);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Protection"
        description="Observation status, rules, incidents, and quarantine for this server. Enforcement stays locked."
      />
      {summary ? (
        <SecurityPanel initial={summary} guildId={params.guildId} isRoot={isRoot} />
      ) : (
        <p className="text-small text-fg-3">Security state is unavailable for this server.</p>
      )}
    </div>
  );
}
