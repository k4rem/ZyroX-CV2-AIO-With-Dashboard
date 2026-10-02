import React from "react";
import { AutomodPage } from "@/components/dashboard/automod-page";

export default function Page({ params }: { params: { guildId: string } }) {
  return <AutomodPage guildId={params.guildId} tab="strikes" />;
}
