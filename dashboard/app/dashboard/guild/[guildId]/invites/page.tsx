"use client";

import React, { useEffect, useState } from "react";
import { PageHeader } from "@/components/dashboard/page-header";
import { api } from "@/lib/api";

type Join = { user_id: string; code: string | null; status: string; joined_at: string };

export default function InvitesPage({ params }: { params: { guildId: string } }) {
  const [rows, setRows] = useState<Join[]>([]);

  useEffect(() => {
    void api.getInvitesV2(params.guildId).then((body) => setRows(body?.joins ?? [])).catch(() => setRows([]));
  }, [params.guildId]);

  return (
    <div className="space-y-4">
      <PageHeader title="Invites" description="History starts when V2 tracking is active. Older counters are not used." />
      {rows.length === 0 ? (
        <p className="text-small text-fg-3">No joins recorded yet.</p>
      ) : (
        <ul className="divide-y divide-line-subtle border border-line-subtle">
          {rows.map((row) => (
            <li key={`${row.user_id}-${row.joined_at}`} className="grid grid-cols-1 gap-1 px-3 py-2 font-mono text-small md:grid-cols-4">
              <span>{row.joined_at.slice(0, 16)}</span>
              <span>{row.user_id}</span>
              <span>{row.code ?? "—"}</span>
              <span>{row.status}</span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
