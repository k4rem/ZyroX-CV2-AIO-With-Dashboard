"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/dashboard/page-header";
import { TicketsNav } from "@/components/dashboard/tickets/tickets-nav";
import { Button } from "@/components/ui/button";

function explain(err: unknown) {
  return err instanceof Error ? err.message : "That panel action failed.";
}

export function PanelsView({
  guildId,
  panels,
  categories,
  channelNames,
}: {
  guildId: string;
  panels: Array<Record<string, any>>;
  categories: Array<{ id: string; name: string }>;
  channelNames: Record<string, string>;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const base = `/dashboard/guild/${guildId}/tickets/panels`;

  async function createPanel() {
    if (!categories[0]) {
      toast.error("Create a team before a panel");
      return;
    }
    setBusy(true);
    try {
      const created = await api.createTicketPanel(guildId, {
        category_id: categories[0].id,
        title: "Contact us",
        message: "Tell us what happened.",
        button_label: "Open ticket",
        questions: [
          { label: "Order number", kind: "short", required: true, min_length: 1, max_length: 40 },
          { label: "Describe the issue", kind: "paragraph", required: false, max_length: 500 },
        ],
        payload: { content: "", embeds: [{ title: "Contact us", description: "Tell us what happened.", color: "#9474ff", footer: { text: "CLS Tickets" } }], buttons: [] },
      });
      router.push(`${base}/${created.id}`);
    } catch (err) {
      toast.error(explain(err));
    } finally {
      setBusy(false);
    }
  }

  async function run(task: () => Promise<unknown>, done: string) {
    setBusy(true);
    try {
      await task();
      toast.success(done);
      router.refresh();
    } catch (err) {
      toast.error(explain(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <TicketsNav guildId={guildId} />
      <PageHeader title="Panels" description="Each panel is the message members use to open a ticket.">
        <Button type="button" disabled={busy} onClick={() => void createPanel()}>New panel</Button>
      </PageHeader>
      {panels.length === 0 ? (
        <p className="border border-line-subtle px-3 py-6 text-small text-fg-3">Create your first ticket panel.</p>
      ) : (
        <ul className="divide-y divide-line-subtle border border-line-subtle">
          {panels.map((panel) => {
            const team = categories.find((item) => item.id === panel.category_id)?.name || "Team";
            const channel = panel.channel_id ? channelNames[panel.channel_id] || "Channel" : "No channel";
            const status = panel.publish_status === "published" ? "Published" : panel.publish_status === "missing" ? "Message missing" : "Draft";
            return (
              <li key={panel.id} className="grid gap-2 px-3 py-2 sm:grid-cols-[minmax(0,1fr)_auto] sm:items-center">
                <div className="min-w-0">
                  <p className="truncate text-small text-fg-1">{panel.title}</p>
                  <p className="truncate text-caption text-fg-3">{team} · #{channel.replace(/^#/, "")} · {status}{panel.published_at ? ` · synced ${new Date(panel.published_at).toLocaleString()}` : ""}</p>
                </div>
                <div className="flex flex-wrap gap-1">
                  <Button type="button" size="sm" variant="secondary" onClick={() => router.push(`${base}/${panel.id}`)}>Edit</Button>
                  <Button type="button" size="sm" variant="ghost" disabled={busy} onClick={() => void run(() => api.duplicateTicketPanel(guildId, panel.id), "Panel duplicated")}>Duplicate</Button>
                  <Button type="button" size="sm" variant="ghost" disabled={busy || !panel.channel_id} onClick={() => void run(() => api.publishTicketPanel(guildId, panel.id, { mode: panel.published_message_id ? "update" : "publish" }), "Panel published")}>{panel.published_message_id ? "Update" : "Publish"}</Button>
                  <Button type="button" size="sm" variant="ghost" disabled={busy || !panel.channel_id} onClick={() => void run(() => api.publishTicketPanel(guildId, panel.id, { mode: "resend" }), "Panel resent")}>Resend</Button>
                  <Button type="button" size="sm" variant="danger-secondary" disabled={busy} onClick={() => void run(() => api.deleteTicketPanel(guildId, panel.id), "Panel deleted")}>Delete</Button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
