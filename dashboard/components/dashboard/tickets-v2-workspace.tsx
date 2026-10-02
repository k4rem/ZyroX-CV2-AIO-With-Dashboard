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
import { ChannelPicker, RolePicker, type ChannelOption } from "@/components/discord/channel-picker";
import { ApiError, api } from "@/lib/api";

type Workspace = {
  open_now: number;
  opened: number;
  closed: number;
  cooldown_seconds: number;
  max_open: number;
  auto_close_hours?: number | null;
  grace_minutes?: number;
  transcript_channel_id?: string | null;
  blacklist: string[];
  categories: Array<{ id: string; name: string; discord_category_id: string | null; staff_role_ids?: string[]; ping_staff?: boolean }>;
  panels: Array<{
    id: string;
    title: string;
    message: string;
    button_label: string;
    channel_id?: string | null;
    published_message_id?: string | null;
    publish_status?: string;
    preview: { message: string; components: Array<{ label: string }> };
  }>;
  tickets: Array<{ id: string; number: number; status: string; opener_id: string; assignee_id: string | null; close_reason: string | null }>;
};

function explain(err: unknown) {
  if (err instanceof ApiError) return err.message;
  return "Something went wrong";
}

export function TicketsV2Workspace({
  guildId,
  initial,
  categories,
  roles,
  channels,
}: {
  guildId: string;
  initial: Workspace;
  categories: Array<{ id: string; name: string }>;
  roles: Array<{ id: string; name: string }>;
  channels: ChannelOption[];
}) {
  const [data, setData] = useState(initial);
  const [name, setName] = useState("");
  const [discordCategory, setDiscordCategory] = useState<string | null>(null);
  const [staffRoles, setStaffRoles] = useState<string[]>([]);
  const [staffPick, setStaffPick] = useState("");
  const [categoryId, setCategoryId] = useState<string | null>(initial.categories[0]?.id ?? null);
  const [title, setTitle] = useState("Contact us");
  const [message, setMessage] = useState("Tell us what happened.");
  const [panelChannel, setPanelChannel] = useState("");
  const [requiredRole, setRequiredRole] = useState("");
  const [blockedRole, setBlockedRole] = useState("");
  const [questions, setQuestions] = useState([
    { label: "Order number", kind: "short", required: true },
    { label: "Describe the issue", kind: "paragraph", required: false },
  ]);
  const [selected, setSelected] = useState<string | null>(null);
  const [lines, setLines] = useState<Array<{ author_id: string; body: string }>>([]);
  const [cooldown, setCooldown] = useState(String(initial.cooldown_seconds ?? 60));
  const [maxOpen, setMaxOpen] = useState(String(initial.max_open ?? 1));
  const [autoClose, setAutoClose] = useState(initial.auto_close_hours ? String(initial.auto_close_hours) : "");
  const [grace, setGrace] = useState(String(initial.grace_minutes ?? 60));
  const [transcriptChannel, setTranscriptChannel] = useState(initial.transcript_channel_id || "");
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
    await api.createTicketCategory(guildId, {
      name,
      discord_category_id: discordCategory,
      staff_role_ids: staffRoles,
      ping_staff: true,
      name_format: "ticket-{number}-{username}",
    });
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
      channel_id: panelChannel || null,
      title,
      message,
      button_label: "Open ticket",
      required_role_ids: requiredRole ? [requiredRole] : [],
      blocked_role_ids: blockedRole ? [blockedRole] : [],
      questions: questions.filter((item) => item.label.trim()).map((item) => ({
        label: item.label,
        kind: item.kind,
        required: item.required,
        min_length: 0,
        max_length: item.kind === "paragraph" ? 1000 : 100,
      })),
    });
    await refresh();
    toast.success("Panel saved");
  };

  const publish = async (panelId: string, mode: string) => {
    try {
      const saved = await api.publishTicketPanel(guildId, panelId, { channel_id: panelChannel || null, mode });
      toast.success(saved.publish_status === "missing" ? "Discord message is missing" : "Panel published");
      await refresh();
    } catch (err) {
      toast.error(explain(err));
    }
  };

  const openTranscript = async (ticketId: string) => {
    const body = await api.getTicketTranscript(guildId, ticketId);
    setSelected(ticketId);
    setLines(body?.lines ?? []);
  };

  const preview = data.panels[0]?.preview;

  return (
    <div className="space-y-6 pb-8">
      <PageHeader title="Tickets" description="Panels, live tickets, and stored transcripts for this server." />
      <dl className="grid grid-cols-3 border border-line-subtle">
        <Readout label="Open now">{data.open_now}</Readout>
        <Readout label="Opened">{data.opened}</Readout>
        <Readout label="Closed">{data.closed}</Readout>
      </dl>

      <div className="grid gap-4 lg:grid-cols-[16rem_minmax(0,1fr)_18rem]">
        <SettingGroup id="ticket-palette" label="Setup">
          <Input value={name} onChange={(event) => setName(event.target.value)} placeholder="Category name" aria-label="Category name" />
          <Combobox
            id="discord-category"
            value={discordCategory}
            options={categories.map((item) => ({ value: item.id, label: item.name, glyph: "category" }))}
            onValueChange={setDiscordCategory}
            placeholder="Discord category"
          />
          <p className="text-small text-fg-3">Support roles</p>
          <RolePicker roles={roles} value={staffPick} onChange={(id) => { setStaffPick(id); setStaffRoles((current) => current.includes(id) ? current : [...current, id]); }} />
          {staffRoles.length > 0 && <p className="text-small text-fg-3">{staffRoles.map((id) => roles.find((role) => role.id === id)?.name || "Role").join(", ")}</p>}
          <Button type="button" variant="secondary" onClick={() => void addCategory()}>Save category</Button>
          <Combobox
            id="ticket-category"
            value={categoryId}
            options={data.categories.map((item) => ({ value: item.id, label: item.name }))}
            onValueChange={setCategoryId}
            placeholder="Ticket category"
          />
          <Input value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Panel title" aria-label="Panel title" />
          <Textarea value={message} onChange={(event) => setMessage(event.target.value)} aria-label="Panel message" />
          <ChannelPicker channels={channels} value={panelChannel} onChange={setPanelChannel} />
          <p className="text-small text-fg-3">Required role</p>
          <RolePicker roles={roles} value={requiredRole} onChange={setRequiredRole} />
          <p className="text-small text-fg-3">Blocked role</p>
          <RolePicker roles={roles} value={blockedRole} onChange={setBlockedRole} />
          {questions.map((question, index) => (
            <div key={index} className="space-y-1">
              <Input
                value={question.label}
                aria-label={`Question ${index + 1}`}
                onChange={(event) => setQuestions((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, label: event.target.value } : item))}
              />
              <div className="flex gap-2 text-small text-fg-3">
                <button type="button" onClick={() => setQuestions((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, kind: "short" } : item))}>{question.kind === "short" ? "Short" : "Use short"}</button>
                <button type="button" onClick={() => setQuestions((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, kind: "paragraph" } : item))}>{question.kind === "paragraph" ? "Paragraph" : "Use paragraph"}</button>
                <button type="button" onClick={() => setQuestions((current) => current.map((item, itemIndex) => itemIndex === index ? { ...item, required: !item.required } : item))}>{question.required ? "Required" : "Optional"}</button>
              </div>
            </div>
          ))}
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
          <ul className="mt-3 space-y-2">
            {data.panels.map((panel) => (
              <li key={panel.id} className="space-y-1 border border-line-subtle p-2">
                <p className="text-small text-fg-1">{panel.title}</p>
                <p className="text-small text-fg-3">{panel.publish_status === "published" ? "Published" : panel.publish_status === "missing" ? "Missing on Discord" : "Not published"}</p>
                <div className="flex flex-wrap gap-1">
                  <Button type="button" size="sm" variant="secondary" onClick={() => void publish(panel.id, panel.published_message_id ? "update" : "publish")}>{panel.published_message_id ? "Update" : "Publish"}</Button>
                  <Button type="button" size="sm" variant="ghost" onClick={() => void publish(panel.id, "resend")}>Resend</Button>
                </div>
              </li>
            ))}
          </ul>
        </SettingGroup>

        <SettingGroup id="ticket-live" label="Live" meta={String(data.tickets.length)}>
          {data.tickets.length === 0 ? (
            <p className="text-small text-fg-3">No tickets stored yet.</p>
          ) : (
            <ul className="space-y-2">
              {data.tickets.map((ticket) => (
                <li key={ticket.id}>
                  <button type="button" className="text-left text-small text-fg-1" onClick={() => void openTranscript(ticket.id)}>
                    #{ticket.number} · {ticket.status}{ticket.close_reason ? ` · ${ticket.close_reason}` : ""}
                  </button>
                </li>
              ))}
            </ul>
          )}
        </SettingGroup>
      </div>

      <SettingGroup id="ticket-limits" label="Limits" meta={`${data.blacklist?.length ?? 0} blocked`}>
        <div className="flex flex-wrap items-center gap-2">
          <Input value={cooldown} onChange={(event) => setCooldown(event.target.value)} aria-label="Cooldown seconds" placeholder="Cooldown seconds" className="w-36" />
          <Input value={maxOpen} onChange={(event) => setMaxOpen(event.target.value)} aria-label="Max open tickets" placeholder="Max open" className="w-28" />
          <Input value={autoClose} onChange={(event) => setAutoClose(event.target.value)} aria-label="Auto-close hours" placeholder="Auto-close hours" className="w-36" />
          <Input value={grace} onChange={(event) => setGrace(event.target.value)} aria-label="Grace minutes" placeholder="Grace minutes" className="w-32" />
          <Button
            type="button"
            variant="secondary"
            onClick={() => void api.updateTicketLimits(guildId, {
              cooldown_seconds: Number(cooldown) || 0,
              max_open: Number(maxOpen) || 1,
              auto_close_hours: autoClose.trim() ? Number(autoClose) : 0,
              grace_minutes: Number(grace) || 60,
              transcript_channel_id: transcriptChannel || null,
            }).then(refresh).catch((err) => toast.error(explain(err)))}
          >
            Save limits
          </Button>
        </div>
        <ChannelPicker channels={channels} value={transcriptChannel} onChange={setTranscriptChannel} />
        <div className="flex flex-wrap items-center gap-2">
          <Input value={blockedUser} onChange={(event) => setBlockedUser(event.target.value)} placeholder="User ID to block" />
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              if (!/^\d{17,22}$/.test(blockedUser)) {
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
