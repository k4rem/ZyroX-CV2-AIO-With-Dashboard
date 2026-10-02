"use client";

import React from "react";
import { InviteManager } from "@/components/dashboard/invite-manager";

export default function InvitesPage({ params }: { params: { guildId: string } }) {
  return <InviteManager guildId={params.guildId} />;
}
