"use client";

import React from "react";
import { GiveawayManager } from "@/components/dashboard/giveaway-manager";

export default function GiveawaysPage({ params }: { params: { guildId: string } }) {
  return <GiveawayManager guildId={params.guildId} />;
}
