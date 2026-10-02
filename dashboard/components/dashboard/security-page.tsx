import React from "react";
import { SecurityWorkspace, type SecurityTab } from "@/components/dashboard/security-workspace";
import { LoadError } from "@/components/platform/load-error";
import { api } from "@/lib/api";
import { authOptions } from "@/lib/auth";
import { isRootOwner } from "@/lib/utils";
import { getServerSession } from "next-auth/next";

export async function SecurityPage({ guildId, tab }: { guildId: string; tab: SecurityTab }) {
  try {
    const [summary, session, channels] = await Promise.all([
      api.getSecurity(guildId),
      getServerSession(authOptions),
      api.getChannels(guildId).catch(() => []),
    ]);
    return (
      <SecurityWorkspace
        guildId={guildId}
        tab={tab}
        initial={summary}
        isRoot={isRootOwner(session?.user?.id)}
        channels={channels ?? []}
      />
    );
  } catch (error) {
    return <LoadError title="Security Center could not be loaded" error={error} />;
  }
}
