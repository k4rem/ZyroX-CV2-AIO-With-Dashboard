"use client";

import React, { useEffect, useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api } from "@/lib/api";

type Row = { id: string; prize: string; status: string; ends_at: string; winner_ids: string[] };

export default function GiveawaysPage({ params }: { params: { guildId: string } }) {
  const [rows, setRows] = useState<Row[]>([]);
  const [prize, setPrize] = useState("");
  const [ends, setEnds] = useState("");

  const load = async () => {
    const body = await api.getGiveaways(params.guildId);
    setRows(body?.giveaways ?? []);
  };

  useEffect(() => {
    void load().catch(() => setRows([]));
  }, [params.guildId]);

  return (
    <div className="space-y-4">
      <PageHeader title="Giveaways" description="Stored giveaways stay open across restarts. No payments." />
      <div className="flex flex-wrap gap-2">
        <Input value={prize} onChange={(event) => setPrize(event.target.value)} placeholder="Prize" />
        <Input type="datetime-local" value={ends} onChange={(event) => setEnds(event.target.value)} />
        <Button
          type="button"
          onClick={() => {
            if (!prize.trim() || !ends) return;
            void api
              .createGiveaway(params.guildId, { prize, ends_at: new Date(ends).toISOString() })
              .then(load)
              .then(() => toast.success("Giveaway saved"))
              .catch(() => toast.error("Could not save the giveaway"));
          }}
        >
          Create
        </Button>
      </div>
      {rows.length === 0 ? <p className="text-small text-fg-3">No giveaways stored.</p> : null}
      <ul className="space-y-2">
        {rows.map((row) => (
          <li key={row.id} className="flex flex-wrap items-center gap-3 border border-line-subtle px-3 py-2 text-small">
            <span>{row.prize}</span>
            <span className="font-mono text-fg-3">{row.status}</span>
            <span className="font-mono">{row.winner_ids.join(", ") || "no winner"}</span>
            {row.status === "open" ? (
              <Button type="button" variant="secondary" onClick={() => void api.endGiveaway(params.guildId, row.id).then(load)}>
                End
              </Button>
            ) : (
              <Button type="button" variant="secondary" onClick={() => void api.rerollGiveaway(params.guildId, row.id).then(load)}>
                Reroll
              </Button>
            )}
          </li>
        ))}
      </ul>
    </div>
  );
}
