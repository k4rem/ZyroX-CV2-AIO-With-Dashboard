import React from "react";
import { CustomRolesWorkspace } from "@/components/dashboard/customroles-workspace";
import { LoadError } from "@/components/platform/load-error";
import { api } from "@/lib/api";

export default async function CustomRolesPage({ params }: { params: { guildId: string } }) {
  let config;
  let roles;
  try {
    [config, roles] = await Promise.all([
      api.getCustomRoles(params.guildId),
      api.getRoles(params.guildId),
    ]);
  } catch (error) {
    return <LoadError title="Custom roles could not be loaded" error={error} />;
  }
  const prefix = await api.getPrefix(params.guildId).catch(() => null);
  if (!config) return <LoadError title="Custom roles could not be loaded" />;
  return (
    <CustomRolesWorkspace
      guildId={params.guildId}
      initialConfig={config}
      roles={roles ?? []}
      prefix={prefix?.prefix || ">"}
    />
  );
}
