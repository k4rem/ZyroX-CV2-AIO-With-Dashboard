"use client";

import React, { useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { SettingGroup } from "@/components/settings/setting-group";
import { Button } from "@/components/ui/button";
import { Combobox } from "@/components/ui/combobox";
import { Input } from "@/components/ui/input";
import { Readout } from "@/components/ui/readout";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";

type Workspace = {
  open_now: number;
  opened: number;
  closed: number;
  cooldown_seconds: number;
  max_open: number;
  blacklist: string[];
  categories: Array<{ id: string; name: string; discord_category_id: string | null }>;
  panels: Array<{ id: string; title: string; message: string; button_label: string; preview: { message: string; components: Array<{ label: string }> } }>;
  tickets: Array<{ id: string; number: number; status: string; opener_id: string; assignee_id: string | null; close_reason: string | null }>;
};

export function TicketsV2Workspace({
  guildId,
  initial,
  categories,
}: {
  guildId: string;
  initial: Workspace;
  categories: Array<{ id: string; name: string }>;
}) {
  const [data, setData] = useState(initial);
  const [name, setName] = useState("");
  const [discordCategory, setDiscordCategory] = useState<string | null>(null);
  const [categoryId, setCategoryId] = useState<string | null>(initial.categories[0]?.id ?? null);
  const [title, setTitle] = useState("Support");
  const [message, setMessage] = useState("Tell us what happened.");
  const [question, setQuestion] = useState("What happened?");
  const [selected, setSelected] = useState<string | null>(null);
  const [lines, setLines] = useState<Array<{ author_id: string; body: string }>>([]);
  const [cooldown, setCooldown] = useState(String(initial.cooldown_seconds ?? 60));
  const [blockedUser, setBlockedUser] = useState("");

  const refresh = async () => {
    const next = await api.getTicketsV2(guildId);
    if (next) {
      setData(next);
      if (!categoryId && next.categories?.[0]) setCategoryId(next.categories[0].id);
    }
  };

  const addCategory = async () => {
    if (!name.trim()) return;
    await api.createTicketCategory(guildId, { name, discord_category_id: discordCategory, staff_role_ids: [] });
    setName("");
    await refresh();
    toast.success("Category saved");
  };

  const addPanel = async () => {
    if (!categoryId) {
      toast.error("Choose a ticket category");
      return;
    }
    await api.createTicketPanel(guildId, {
      category_id: categoryId,
      title,
      message,
      button_label: "Open ticket",
      questions: question.trim() ? [{ label: question, kind: "long", required: true }] : [],
    });
    await refresh();
    toast.success("Panel saved");
  };

  const openTranscript = async (ticketId: string) => {
    const body = await api.getTicketTranscript(guildId, ticketId);
    setSelected(ticketId);
    setLines(body?.lines ?? []);
  };

  const preview = data.panels[0]?.preview;

  return (
    <div className="space-y-6">
      <PageHeader title="Tickets" description="Panels, live tickets, and stored transcripts for this server." />
      <dl className="grid grid-cols-3 border border-line-subtle">
        <Readout label="Open now">{data.open_now}</Readout>
        <Readout label="Opened">{data.opened}</Readout>
        <Readout label="Closed">{data.closed}</Readout>
      </dl>
      {data.opened < 2 ? (
        <p className="text-small text-fg-3">Not enough stored tickets to draw a trend. Counts above are the real totals.</p>
      ) : null}

      <div className="grid gap-4 lg:grid-cols-[16rem_minmax(0,1fr)_18rem]">
        <SettingGroup id="ticket-palette" label="Setup">
          <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="Category name" />
          <Combobox
            id="discord-category"
            value={discordCategory}
            options={categories.map((item) => ({ value: item.id, label: item.name, glyph: "category" }))}
            onValueChange={setDiscordCategory}
            placeholder="Discord category"
          />
          <Button type="button" variant="secondary" onClick={() => void addCategory()}>Save category</Button>
          <Combobox
            id="ticket-category"
            value={categoryId}
            options={data.categories.map((item) => ({ value: item.id, label: item.name }))}
            onValueChange={setCategoryId}
            placeholder="Ticket category"
          />
          <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Panel title" />
          <Textarea value={message} onChange={(event) => setMessage(event.target.value)} />
          <Input value={question} onChange={(event) => setQuestion(event.target.value)} placeholder="Form question" />
          <Button type="button" onClick={() => void addPanel()}>Save panel</Button>
        </SettingGroup>

        <SettingGroup id="ticket-preview" label="Discord preview">
          {preview ? (
            <div className="border border-line-subtle bg-surface-1 p-3">
              <p className="text-small text-fg-1">{preview.message}</p>
              <span className="mt-3 inline-block border border-line-subtle px-2 py-1 text-small">{preview.components[0]?.label}</span>
            </div>
          ) : (
            <p className="text-small text-fg-3">Save a panel to preview the Discord message.</p>
          )}
        </SettingGroup>

        <SettingGroup id="ticket-live" label="Live" meta={String(data.tickets.length)}>
          {data.tickets.length === 0 ? (
            <p className="text-small text-fg-3">No tickets stored yet.</p>
          ) : (
            <ul className="space-y-2">
              {data.tickets.map((ticket) => (
                <li key={ticket.id}>
                  <button type="button" className="text-left font-mono text-small text-fg-1" onClick={() => void openTranscript(ticket.id)}>
                    #{ticket.number} · {ticket.status} · {ticket.opener_id}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </SettingGroup>
      </div>

      <SettingGroup id="ticket-limits" label="Limits" meta={`${data.blacklist?.length ?? 0} blocked`}>
        <div className="flex flex-wrap items-center gap-2">
          <Input value={cooldown} onChange={(event) => setCooldown(event.target.value)} placeholder="Cooldown seconds" />
          <Button
            type="button"
            variant="secondary"
            onClick={() => void api.updateTicketLimits(guildId, { cooldown_seconds: Number(cooldown) || 0, max_open: data.max_open || 1 }).then(refresh)}
          >
            Save cooldown
          </Button>
          <Input value={blockedUser} onChange={(event) => setBlockedUser(event.target.value)} placeholder="User ID to block" />
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              if (!/^\d{17,20}$/.test(blockedUser)) {
                toast.error("Enter a Discord user ID");
                return;
              }
              void api.blacklistTicketUser(guildId, blockedUser).then(() => {
                setBlockedUser("");
                return refresh();
              });
            }}
          >
            Blacklist
          </Button>
        </div>
        {data.blacklist?.length ? (
          <p className="font-mono text-small text-fg-3">{data.blacklist.join(", ")}</p>
        ) : (
          <p className="text-small text-fg-3">No blacklisted users.</p>
        )}
      </SettingGroup>

      <SettingGroup id="ticket-transcript" label="Transcript">
        {selected === null ? (
          <p className="text-small text-fg-3">Open a ticket to read its stored transcript.</p>
        ) : lines.length === 0 ? (
          <p className="text-small text-fg-3">This ticket has no stored lines.</p>
        ) : (
          <ul className="space-y-2">
            {lines.map((line, index) => (
              <li key={`${line.author_id}-${index}`} className="text-small text-fg-1">
                <span className="font-mono text-fg-3">{line.author_id}</span> {line.body}
              </li>
            ))}
          </ul>
        )}
      </SettingGroup>
    </div>
  );
}
