import React from "react";
import { PageHeader } from "@/components/dashboard/page-header";
import { ConfigTransfer } from "@/components/dashboard/config-transfer";

export default function ConfigTransferPage({ params }: { params: { guildId: string } }) {
  return (
    <div>
      <PageHeader title="Backup & Transfer" description="Download this server's configuration, or restore a backup here. History and secrets stay out of the file." />
      <ConfigTransfer guildId={params.guildId} />
    </div>
  );
}
