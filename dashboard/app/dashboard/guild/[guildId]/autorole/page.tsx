import React from "react";
import dynamic from "next/dynamic";
import { PageHeader } from "@/components/dashboard/page-header";
import { api } from "@/lib/api";

const AutoRoleForm = dynamic(() => import("@/components/dashboard/autorole-form").then((mod) => mod.AutoRoleForm), {
  loading: () => <div className="h-24 w-full animate-pulse rounded-md bg-surface-2" />,
});

export default async function AutoRolePage({ params }: { params: { guildId: string } }) {
  const [config, roles] = await Promise.all([api.getAutoRole(params.guildId), api.getRoles(params.guildId)]);

  return (
    <div>
      <PageHeader title="Auto roles" description="Roles assigned when someone joins this server." />
      <AutoRoleForm initialConfig={config} roles={roles} guildId={params.guildId} />
    </div>
  );
}
