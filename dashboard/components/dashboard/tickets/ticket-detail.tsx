"use client";

import { useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { ageLabel, eventLabel, ticketStatusLabel } from "@/lib/ticketsModel";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { MemberPicker, type MemberChoice } from "@/components/discord/member-picker";

function explain(err: unknown) {
  return err instanceof Error ? err.message : "That action did not complete.";
}

export function Conversation({ messages }: { messages: Array<Record<string, any>> }) {
  if (!messages.length) return <p className="text-small text-fg-3">No messages were stored.</p>;
  return (
    <ol className="space-y-3">
      {messages.map((message) => (
        <li key={message.id || message.created_at} className="grid grid-cols-[28px_minmax(0,1fr)] gap-2">
          {message.avatar ? <img src={message.avatar} alt="" className="size-7 rounded-full" /> : <span className="size-7 rounded-full bg-surface-2" />}
          <div className="min-w-0">
            <p className="text-small text-fg-1">
              <span className="font-medium">{message.display_name || "Member"}</span>
              <time className="ms-2 text-fg-3">{message.created_at ? new Date(message.created_at).toLocaleString() : ""}</time>
            </p>
            {message.reference_id && <p className="text-caption text-fg-3">Reply</p>}
            {message.content && <p className="whitespace-pre-wrap break-words text-small text-fg-2">{message.content}</p>}
            {(message.attachments || []).map((file: { url?: string; filename?: string }) => (
              <a key={file.url} href={file.url} className="block text-small text-accent" target="_blank" rel="noreferrer">{file.filename || "Attachment"}</a>
            ))}
            {(message.embeds || []).map((embed: { title?: string; description?: string }, index: number) => (
              <blockquote key={index} className="mt-1 border-s border-line-subtle ps-2 text-small text-fg-3">
                {embed.title && <strong className="block text-fg-2">{embed.title}</strong>}
                {embed.description}
              </blockquote>
            ))}
          </div>
        </li>
      ))}
    </ol>
  );
}

export function TicketDetail({
  guildId,
  ticket,
  categories,
  onChanged,
}: {
  guildId: string;
  ticket: Record<string, any>;
  categories: Array<{ id: string; name: string }>;
  onChanged: () => void;
}) {
  const [reason, setReason] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [busy, setBusy] = useState(false);
  const answers = ticket.answers && typeof ticket.answers === "object" ? Object.entries(ticket.answers) : [];

  async function act(action: string, extra: Record<string, string> = {}) {
    setBusy(true);
    try {
      await api.actOnTicket(guildId, ticket.id, { action, ...extra });
      toast.success("Ticket updated");
      onChanged();
    } catch (err) {
      toast.error(explain(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="flex h-full min-h-0 flex-col">
      <header className="border-b border-line-subtle px-3 py-2">
        <p className="text-body text-fg-1">Ticket {String(ticket.number).padStart(4, "0")}</p>
        <p className="text-small text-fg-3">{ticketStatusLabel(ticket.status)} · {ticket.category_name || "Team"}</p>
      </header>
      <div className="min-h-0 flex-1 space-y-4 overflow-y-auto px-3 py-3">
        <dl className="grid grid-cols-2 gap-x-3 gap-y-2 text-small">
          <div><dt className="text-fg-3">Opened by</dt><dd className="text-fg-1">{ticket.opener_name || "Member"}</dd></div>
          <div><dt className="text-fg-3">Assignee</dt><dd className="text-fg-1">{ticket.assignee_name || "Unassigned"}</dd></div>
          <div><dt className="text-fg-3">Opened</dt><dd className="text-fg-1">{ageLabel(ticket.opened_at) === "just now" ? "just now" : `${ageLabel(ticket.opened_at)} ago`}</dd></div>
          <div><dt className="text-fg-3">Last activity</dt><dd className="text-fg-1">{ageLabel(ticket.last_activity_at)}</dd></div>
        </dl>
        {ticket.close_reason && <p className="text-small text-fg-2">Close reason: {ticket.close_reason}</p>}
        {answers.length > 0 && (
          <section>
            <h3 className="mb-1 text-caption uppercase tracking-wide text-fg-3">Form</h3>
            {answers.map(([label, value]) => (
              <p key={label} className="text-small text-fg-1"><span className="text-fg-3">{label}. </span>{String(value)}</p>
            ))}
          </section>
        )}
        <section>
          <h3 className="mb-2 text-caption uppercase tracking-wide text-fg-3">Conversation</h3>
          <Conversation messages={ticket.messages || []} />
        </section>
        <section>
          <h3 className="mb-1 text-caption uppercase tracking-wide text-fg-3">Timeline</h3>
          <ol className="space-y-1">
            {(ticket.events || []).map((event: { id: string; created_at?: string; kind?: string; actor_name?: string; payload?: Record<string, unknown> }) => (
              <li key={event.id} className="text-small text-fg-2">
                {eventLabel(event)}
                <time className="ms-2 text-fg-3">{event.created_at ? new Date(event.created_at).toLocaleString() : ""}</time>
              </li>
            ))}
          </ol>
        </section>
        {(ticket.participant_names || []).length > 0 && (
          <section>
            <h3 className="mb-1 text-caption uppercase tracking-wide text-fg-3">Added members</h3>
            {(ticket.participant_names || []).map((person: MemberChoice) => (
              <div key={person.id} className="flex items-center justify-between gap-2 py-1">
                <span className="text-small text-fg-1">{person.display_name}</span>
                <Button type="button" size="sm" variant="ghost" disabled={busy} onClick={() => void act("remove", { user_id: person.id })}>Remove</Button>
              </div>
            ))}
          </section>
        )}
      </div>
      <footer className="space-y-2 border-t border-line-subtle p-3">
        <div className="flex flex-wrap gap-1">
          {ticket.status === "open" && <Button type="button" size="sm" disabled={busy} onClick={() => void act("claim")}>Claim</Button>}
          {ticket.status === "claimed" && <Button type="button" size="sm" variant="secondary" disabled={busy} onClick={() => void act("unclaim")}>Unclaim</Button>}
          {ticket.raw_status === "closed" && <Button type="button" size="sm" disabled={busy} onClick={() => void act("reopen")}>Reopen</Button>}
        </div>
        {ticket.raw_status === "open" && (
          <>
            <div className="flex gap-1">
              <Input value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Close reason" aria-label="Close reason" />
              <Button type="button" size="sm" variant="danger" disabled={busy || !reason.trim()} onClick={() => void act("close", { reason })}>Close</Button>
            </div>
            <div className="flex gap-1">
              <Select value={categoryId} onValueChange={setCategoryId} placeholder="Transfer to" options={categories.filter((item) => item.id !== ticket.category_id).map((item) => ({ value: item.id, label: item.name }))} />
              <Button type="button" size="sm" variant="secondary" disabled={busy || !categoryId} onClick={() => void act("transfer", { category_id: categoryId })}>Transfer</Button>
            </div>
            <MemberPicker guildId={guildId} onSelect={(member) => void act("add", { user_id: member.id })} />
          </>
        )}
      </footer>
    </div>
  );
}
