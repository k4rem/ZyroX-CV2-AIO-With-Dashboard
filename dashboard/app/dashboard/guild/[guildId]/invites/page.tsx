"use client";

import React, { useState, useEffect } from "react";
import { TrendingUp, RefreshCcw, User } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/dashboard/page-header";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Button } from "@/components/ui/button";

export default function InvitesPage({ params }: { params: { guildId: string } }) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState<
    { user_id: string; total: number; left: number; fake: number; rejoin: number }[]
  >([]);

  const fetchLeaderboard = async () => {
    try {
      setLoading(true);
      const res = await api.getInvites(params.guildId);
      setData(res.data || []);
    } catch (error) {
      console.error("Failed to fetch invites leaderboard:", error);
      toast.error("Failed to load invites leaderboard");
      setData([]);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void fetchLeaderboard();
  }, [params.guildId]);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Invites"
        description="Legacy invite counters from the bot tracker. Counts are not independently verified."
      >
        <Button variant="secondary" size="sm" onClick={() => void fetchLeaderboard()} disabled={loading}>
          <RefreshCcw className={`size-4 ${loading ? "animate-spin" : ""}`} aria-hidden="true" />
          Refresh
        </Button>
      </PageHeader>

      <p className="rounded-md border border-warn/30 bg-warn/[0.08] px-3 py-2 text-caption text-fg-2">
        Legacy counts, unverified — use for orientation only until Invites V2.
      </p>

      {loading ? (
        <p className="text-body text-fg-2">Loading invite data…</p>
      ) : data.length === 0 ? (
        <p className="text-body text-fg-2">No invite data available.</p>
      ) : (
        <div className="overflow-x-auto rounded-md border border-line bg-surface-1">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Rank</TableHead>
                <TableHead>User</TableHead>
                <TableHead className="text-end">Total</TableHead>
                <TableHead className="hidden text-end sm:table-cell">Real</TableHead>
                <TableHead className="hidden text-end md:table-cell">Left</TableHead>
                <TableHead className="hidden text-end lg:table-cell">Fake</TableHead>
                <TableHead className="hidden text-end lg:table-cell">Rejoin</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {data.map((row, index) => (
                <TableRow key={row.user_id ?? index}>
                  <TableCell className="tabular-nums text-fg-2">{index + 1}</TableCell>
                  <TableCell>
                    <span className="inline-flex items-center gap-2 font-mono text-body text-fg-1" dir="ltr">
                      <User className="size-4 text-fg-3" aria-hidden="true" />
                      {row.user_id}
                    </span>
                  </TableCell>
                  <TableCell className="text-end tabular-nums">{row.total}</TableCell>
                  <TableCell className="hidden text-end tabular-nums sm:table-cell">
                    {row.total - row.left - row.fake - row.rejoin}
                  </TableCell>
                  <TableCell className="hidden text-end tabular-nums md:table-cell">{row.left}</TableCell>
                  <TableCell className="hidden text-end tabular-nums lg:table-cell">{row.fake}</TableCell>
                  <TableCell className="hidden text-end tabular-nums lg:table-cell">{row.rejoin}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      )}
    </div>
  );
}
