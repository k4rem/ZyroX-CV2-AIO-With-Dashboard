"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function TrackingPage({ params }: { params: { guildId: string } }) {
  const router = useRouter();
  useEffect(() => {
    router.replace(`/dashboard/guild/${params.guildId}/invites`);
  }, [params.guildId, router]);
  return null;
}
