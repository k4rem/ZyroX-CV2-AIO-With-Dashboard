"use client";

import React from "react";
import { AutoReactManager } from "@/components/dashboard/autoreact-manager";

export default function AutoReactPage({ params }: { params: { guildId: string } }) {
  return <AutoReactManager guildId={params.guildId} />;
}
