"use client";

import { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { ageLabel, filterTickets, ticketStatusLabel, type TicketRow } from "@/lib/ticketsModel";
import { PageHeader } from "@/components/dashboard/page-header";
import { TicketsNav } from "@/components/dashboard/tickets/tickets-nav";
import { TicketDetail } from "@/components/dashboard/tickets/ticket-detail";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { Drawer, DrawerContent } from "@/components/ui/drawer";

export function QueueView({
  guildId,
  initial,
  categories,
}: {
  guildId: string;
  initial: TicketRow[];
  categories: Array<{ id: string; name: string }>;
}) {
  const [rows, setRows] = useState<TicketRow[]>(initial);
  const [status, setStatus] = useState("all");
  const [categoryId, setCategoryId] = useState("all");
  const [assignee, setAssignee] = useState("all");
  const [query, setQuery] = useState("");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [detail, setDetail] = useState<Record<string, any> | null>(null);
  const [narrow, setNarrow] = useState(false);

  async function refresh() {
    const body = await api.getTicketQueue(guildId);
    setRows(body.tickets || []);
  }

  useEffect(() => {
    const timer = window.setInterval(() => void refresh().catch(() => undefined), 12000);
    return () => window.clearInterval(timer);
  }, [guildId]);

  useEffect(() => {
    const media = window.matchMedia("(max-width: 1023px)");
    const sync = () => setNarrow(media.matches);
    sync();
    media.addEventListener("change", sync);
    return () => media.removeEventListener("change", sync);
  }, []);

  useEffect(() => {
    if (!selectedId) {
      setDetail(null);
      return;
    }
    api.getTicketDetail(guildId, selectedId).then(setDetail).catch(() => setDetail(null));
  }, [guildId, selectedId, rows]);

  const assignees = useMemo(() => Array.from(new Set(rows.map((row) => row.assignee_name).filter(Boolean))) as string[], [rows]);
  const visible = filterTickets(rows, { status, categoryId, assignee, query });

  return (
    <div>
      <TicketsNav guildId={guildId} />
      <PageHeader title="Queue" description="Open tickets and the people waiting on them." />
      <div className="mb-3 grid gap-2 sm:grid-cols-4">
        <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search number, opener, or reason" aria-label="Search tickets" />
        <Select value={status} onValueChange={setStatus} options={[{ value: "all", label: "Any status" }, { value: "open", label: "Open" }, { value: "claimed", label: "Claimed" }, { value: "closed", label: "Closed" }]} />
        <Select value={categoryId} onValueChange={setCategoryId} options={[{ value: "all", label: "Any team" }, ...categories.map((item) => ({ value: item.id, label: item.name }))]} />
        <Select value={assignee} onValueChange={setAssignee} options={[{ value: "all", label: "Any assignee" }, { value: "unassigned", label: "Unassigned" }, ...assignees.map((name) => ({ value: name, label: name }))]} />
      </div>
      <div className="grid gap-3 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="min-w-0">
          {visible.length === 0 ? (
            <p className="border border-line-subtle px-3 py-6 text-small text-fg-3">{rows.length === 0 ? "No tickets need attention." : "Nothing matches these filters."}</p>
          ) : (
            <ul className="divide-y divide-line-subtle border border-line-subtle">
              {visible.map((ticket) => (
                <li key={ticket.id}>
                  <button type="button" className={`grid w-full grid-cols-[auto_minmax(0,1fr)_auto] items-center gap-3 px-3 py-2 text-left ${selectedId === ticket.id ? "bg-surface-2" : "hover:bg-surface-1"}`} onClick={() => setSelectedId(ticket.id)}>
                    <span className="text-small text-fg-3">#{ticket.number}</span>
                    <span className="min-w-0">
                      <span className="flex items-center gap-2 text-small text-fg-1">
                        {ticket.opener_avatar ? <img src={ticket.opener_avatar} alt="" className="size-5 rounded-full" /> : <span className="size-5 rounded-full bg-surface-2" />}
                        <span className="truncate">{ticket.opener_name || "Member"}</span>
                        <span className="text-fg-3">{ticketStatusLabel(ticket.status)}</span>
                      </span>
                      <span className="block truncate text-caption text-fg-3">{ticket.category_name || "Team"} · {ticket.assignee_name || "Unassigned"}</span>
                    </span>
                    <span className="text-end text-caption text-fg-3">
                      <span className="block">{ageLabel(ticket.opened_at)}</span>
                      <span className="block">active {ageLabel(ticket.last_activity_at)}</span>
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>
        <aside className="hidden min-h-[28rem] border border-line-subtle lg:block">
          {detail ? <TicketDetail guildId={guildId} ticket={detail} categories={categories} onChanged={() => void refresh()} /> : <p className="p-3 text-small text-fg-3">Select a ticket.</p>}
        </aside>
      </div>
      <Drawer open={Boolean(selectedId) && narrow} onOpenChange={(open) => { if (!open) setSelectedId(null); }}>
        <DrawerContent title="Ticket" side="end" width="min(100vw, 28rem)" className="lg:hidden">
          {detail && <TicketDetail guildId={guildId} ticket={detail} categories={categories} onChanged={() => void refresh()} />}
        </DrawerContent>
      </Drawer>
    </div>
  );
}
