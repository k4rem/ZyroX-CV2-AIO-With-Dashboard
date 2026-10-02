import React from "react";
import { PageHeader } from "@/components/dashboard/page-header";
import { RoleAutomation } from "@/components/dashboard/role-automation";
import { api } from "@/lib/api";

export default async function AutoRolePage({ params }: { params: { guildId: string } }) {
  const [config, roles] = await Promise.all([api.getRoleAutomation(params.guildId), api.getRoles(params.guildId)]);

  return (
    <div>
      <PageHeader title="Role Automation" description="Join roles and rules that add or remove roles when something happens." />
      <RoleAutomation guildId={params.guildId} join={config.join} rules={config.rules || []} roles={roles} />
    </div>
  );
}
