"use client";

import Link from "next/link";
import { useMemo, useState } from "react";
import { filterTickets, type TicketRow } from "@/lib/ticketsModel";
import { PageHeader } from "@/components/dashboard/page-header";
import { TicketsNav } from "@/components/dashboard/tickets/tickets-nav";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";

export function TranscriptsView({
  guildId,
  rows,
  categories,
}: {
  guildId: string;
  rows: Array<Record<string, any>>;
  categories: Array<{ id: string; name: string }>;
}) {
  const [query, setQuery] = useState("");
  const [categoryId, setCategoryId] = useState("all");
  const [staff, setStaff] = useState("all");
  const names = useMemo(() => Array.from(new Set(rows.map((row) => row.assignee_name).filter(Boolean))) as string[], [rows]);
  const visible = filterTickets(rows as TicketRow[], { status: "all", categoryId, assignee: staff, query });

  return (
    <div>
      <TicketsNav guildId={guildId} />
      <PageHeader title="Transcripts" description="Closed tickets stay here after the Discord channel is gone." />
      <div className="mb-3 grid gap-2 sm:grid-cols-3">
        <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search number, opener, or reason" aria-label="Search transcripts" />
        <Select value={categoryId} onValueChange={setCategoryId} options={[{ value: "all", label: "Any team" }, ...categories.map((item) => ({ value: item.id, label: item.name }))]} />
        <Select value={staff} onValueChange={setStaff} options={[{ value: "all", label: "Any staff" }, ...names.map((name) => ({ value: name, label: name }))]} />
      </div>
      {visible.length === 0 ? (
        <p className="border border-line-subtle px-3 py-6 text-small text-fg-3">Closed ticket transcripts will appear here.</p>
      ) : (
        <ul className="divide-y divide-line-subtle border border-line-subtle">
          {visible.map((row) => (
            <li key={row.id}>
              <Link href={`/dashboard/guild/${guildId}/tickets/transcripts/${row.id}`} className="grid grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 px-3 py-2 hover:bg-surface-1">
                <span className="text-small text-fg-3">#{row.number}</span>
                <span className="min-w-0">
                  <span className="block truncate text-small text-fg-1">{row.opener_name || "Member"} · {row.category_name || "Team"}</span>
                  <span className="block truncate text-caption text-fg-3">{row.close_reason || "No reason"} · {row.assignee_name || "Unassigned"}</span>
                </span>
                <time className="text-caption text-fg-3">{row.closed_at ? new Date(row.closed_at).toLocaleDateString() : ""}</time>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
