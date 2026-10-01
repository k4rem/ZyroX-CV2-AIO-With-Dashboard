import React from "react";
import { CustomRolesWorkspace } from "@/components/dashboard/customroles-workspace";
import { api } from "@/lib/api";

export default async function CustomRolesPage({ params }: { params: { guildId: string } }) {
  const [config, roles, prefix] = await Promise.all([
    api.getCustomRoles(params.guildId),
    api.getRoles(params.guildId),
    api.getPrefix(params.guildId).catch(() => null),
  ]);
  if (!config) return null;
  return (
    <CustomRolesWorkspace
      guildId={params.guildId}
      initialConfig={config}
      roles={roles ?? []}
      prefix={prefix?.prefix || ">"}
    />
  );
}
