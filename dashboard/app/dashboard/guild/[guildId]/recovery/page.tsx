"use client";

import React, { useEffect, useState } from "react";
import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";

export default function RecoveryPage({ params }: { params: { guildId: string } }) {
  const [rows, setRows] = useState<Array<{ id: string; status: string; checksum: string | null }>>([]);
  const [plan, setPlan] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void api.getSnapshots(params.guildId).then(setRows).catch(() => setError("Snapshots are unavailable."));
  }, [params.guildId]);

  return (
    <div className="space-y-4">
      <PageHeader
        title="Recovery"
        description="Dry run builds a restore plan. Execution stays disabled unless this process is explicitly pointed at a disposable guild."
      />
      {error ? <p className="text-small text-fg-3">{error}</p> : null}
      {rows.length === 0 ? <p className="text-small text-fg-3">No snapshots stored for this server.</p> : null}
      <ul className="space-y-2">
        {rows.map((row) => (
          <li key={row.id} className="flex flex-wrap items-center gap-3 border border-line-subtle px-3 py-2">
            <span className="font-mono text-small">{row.status}</span>
            <span className="font-mono text-caption text-fg-3">{row.checksum?.slice(0, 12)}</span>
            <Button
              type="button"
              variant="secondary"
              onClick={() =>
                void api
                  .planRestore(params.guildId, row.id, [])
                  .then(setPlan)
                  .catch(() => setError("Restore planning is Root-only."))
              }
            >
              Dry run
            </Button>
          </li>
        ))}
      </ul>
      {plan ? (
        <pre className="overflow-x-auto whitespace-pre-wrap text-small">{JSON.stringify(plan, null, 2)}</pre>
      ) : null}
    </div>
  );
}
