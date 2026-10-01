"use client";

import React, { useEffect, useMemo, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { ChannelPicker, type ChannelOption } from "@/components/discord/channel-picker";
import type { GuildEmoji } from "@/components/discord/emoji-picker";
import { MessageComposer, type ComposerSelection } from "@/components/discord/message-composer";
import { DiscordMessagePreview } from "@/components/discord/message-preview";
import { Button } from "@/components/ui/button";
import { Dialog, DialogBody, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";
import {
  emptyMessage,
  parseMessageJson,
  previewHint,
  validateMessage,
  type MessageDraft,
} from "@/lib/messagePayload";
import { cn } from "@/lib/utils";

type Template = { id: string; name: string; payload: MessageDraft; updated_at: string };
type SentRow = {
  id: string;
  channel_id: string;
  message_id: string;
  template_id: string | null;
  payload: MessageDraft;
  sent_at: string;
  edited_at: string | null;
  missing: boolean;
  jump_url: string;
};

function explain(err: unknown) {
  if (err instanceof ApiError) return err.message;
  return "Something went wrong";
}

function withParents(channels: ChannelOption[]): ChannelOption[] {
  const names = new Map(channels.filter((channel) => channel.type === "4" || channel.type === "category").map((channel) => [channel.id, channel.name]));
  return channels.map((channel) => ({ ...channel, parent_name: channel.parent_id ? names.get(channel.parent_id) || null : null }));
}

export function MessagesWorkspace({
  guildId,
  templates: initialTemplates,
  sent: initialSent,
  channels,
  emojis,
  values,
  initialTab,
}: {
  guildId: string;
  templates: Template[];
  sent: SentRow[];
  channels: ChannelOption[];
  emojis: GuildEmoji[];
  values: Record<string, string>;
  initialTab?: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [tab, setTab] = useState(initialTab === "sent" || initialTab === "editor" ? initialTab : "library");
  const [pane, setPane] = useState<"edit" | "preview">("edit");
  const [jsonMode, setJsonMode] = useState(false);
  const [jsonText, setJsonText] = useState("");
  const [templates, setTemplates] = useState(initialTemplates);
  const [sent, setSent] = useState(initialSent);
  const [query, setQuery] = useState("");
  const [name, setName] = useState("Untitled message");
  const [message, setMessage] = useState<MessageDraft>(emptyMessage());
  const [templateId, setTemplateId] = useState<string | null>(null);
  const [sentId, setSentId] = useState<string | null>(null);
  const [snapshot, setSnapshot] = useState("");
  const [selection, setSelection] = useState<ComposerSelection>({ kind: "embed", index: 0 });
  const [errors, setErrors] = useState<string[]>([]);
  const [sendOpen, setSendOpen] = useState(false);
  const [channelId, setChannelId] = useState("");
  const [busy, setBusy] = useState(false);
  const channelOptions = useMemo(() => withParents(channels), [channels]);
  const dirty = snapshot !== "" && snapshot !== JSON.stringify({ name, message });

  useEffect(() => {
    if (!snapshot) setSnapshot(JSON.stringify({ name, message }));
  }, [message, name, snapshot]);

  useEffect(() => {
    const warn = (event: BeforeUnloadEvent) => {
      if (!dirty) return;
      event.preventDefault();
      event.returnValue = "";
    };
    window.addEventListener("beforeunload", warn);
    return () => window.removeEventListener("beforeunload", warn);
  }, [dirty]);

  function openTab(next: string) {
    if (tab === "editor" && next !== "editor" && dirty && !window.confirm("Leave without saving changes?")) return;
    setTab(next);
    router.replace(`${pathname}?tab=${next}`);
  }

  function load(nextName: string, nextMessage: MessageDraft, nextTemplate: string | null, nextSent: string | null) {
    setName(nextName);
    setMessage(nextMessage);
    setTemplateId(nextTemplate);
    setSentId(nextSent);
    setSnapshot(JSON.stringify({ name: nextName, message: nextMessage }));
    setErrors([]);
    setJsonMode(false);
    setSelection(nextMessage.embeds.length ? { kind: "embed", index: 0 } : { kind: "content" });
    setTab("editor");
    router.replace(`${pathname}?tab=editor`);
  }

  function changeMessage(next: MessageDraft) {
    setMessage(next);
    setErrors([]);
  }

  async function save(asNew = false) {
    const problems = validateMessage(message);
    setErrors(problems);
    if (problems.length) return;
    setBusy(true);
    try {
      if (!asNew && templateId) {
        const saved = await api.updateMessageTemplate(guildId, templateId, { name, payload: message });
        setTemplates((rows) => rows.map((row) => (row.id === saved.id ? saved : row)));
        setSnapshot(JSON.stringify({ name: saved.name, message: saved.payload }));
        toast.success("Template saved");
      } else {
        const saved = await api.createMessageTemplate(guildId, { name: asNew ? `${name} copy` : name, payload: message });
        setTemplates((rows) => [saved, ...rows]);
        setTemplateId(saved.id);
        setName(saved.name);
        setSnapshot(JSON.stringify({ name: saved.name, message: saved.payload }));
        toast.success(asNew ? "Saved as a new template" : "Template saved");
      }
    } catch (err) {
      toast.error(explain(err));
    } finally {
      setBusy(false);
    }
  }

  async function send() {
    const problems = validateMessage(message);
    setErrors(problems);
    if (problems.length || !channelId) return;
    setBusy(true);
    try {
      const row = await api.sendGuildMessage(guildId, { channel_id: channelId, template_id: templateId, payload: message });
      setSent((rows) => [row, ...rows.filter((item) => item.id !== row.id)]);
      setSentId(row.id);
      setSendOpen(false);
      toast.success("Sent to Discord");
    } catch (err) {
      toast.error(explain(err));
    } finally {
      setBusy(false);
    }
  }

  async function updateDiscord() {
    if (!sentId) return;
    const problems = validateMessage(message);
    setErrors(problems);
    if (problems.length) return;
    setBusy(true);
    try {
      const row = await api.editSentMessage(guildId, sentId, message);
      setSent((rows) => rows.map((item) => (item.id === row.id ? row : item)));
      setSnapshot(JSON.stringify({ name, message: row.payload }));
      setMessage(row.payload);
      toast.success("Discord message updated");
    } catch (err) {
      toast.error(explain(err));
      if (err instanceof ApiError && err.status === 404) {
        setSent((rows) => rows.map((item) => (item.id === sentId ? { ...item, missing: true } : item)));
      }
    } finally {
      setBusy(false);
    }
  }

  async function refreshSent() {
    try {
      const home = await api.listSentMessages(guildId);
      setSent(home.sent);
    } catch (err) {
      toast.error(explain(err));
    }
  }

  const filtered = templates.filter((item) => item.name.toLowerCase().includes(query.trim().toLowerCase()));

  return (
    <div>
      <PageHeader title="Messages" description="Compose, preview, and send Discord messages from CLS.">
        <div className="flex gap-1">
          {["library", "editor", "sent"].map((item) => (
            <button key={item} type="button" onClick={() => openTab(item)} className={cn("h-8 rounded-sm px-3 text-caption capitalize", tab === item ? "bg-surface-3 text-fg-1" : "text-fg-3")}>
              {item === "sent" ? "Sent" : item}
            </button>
          ))}
        </div>
      </PageHeader>

      {tab === "library" && (
        <div className="space-y-3">
          <div className="flex flex-wrap gap-2">
            <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search templates" className="max-w-xs" />
            <Button type="button" variant="primary" onClick={() => load("Untitled message", emptyMessage(), null, null)}>New message</Button>
            <label className="inline-flex h-8 cursor-pointer items-center rounded-sm border border-line-strong bg-surface-3 px-3 text-caption text-fg-1">
              Import JSON
              <input type="file" accept="application/json,.json" className="hidden" onChange={async (event) => {
                const file = event.target.files?.[0];
                event.target.value = "";
                if (!file) return;
                const parsed = parseMessageJson(await file.text());
                if (!parsed.message) {
                  setErrors(parsed.errors);
                  setTab("editor");
                  toast.error(parsed.errors[0] || "Import failed");
                  return;
                }
                load(file.name.replace(/\.json$/i, "") || "Imported message", parsed.message, null, null);
              }} />
            </label>
          </div>
          {filtered.length === 0 && <p className="rounded-md border border-dashed border-line px-3 py-8 text-center text-caption text-fg-3">No templates yet. Create one to send a message.</p>}
          <ul className="divide-y divide-line rounded-md border border-line">
            {filtered.map((item) => (
              <li key={item.id} className="flex flex-wrap items-center gap-2 px-3 py-2">
                <div className="min-w-0 flex-1">
                  <div className="truncate text-body text-fg-1">{item.name}</div>
                  <div className="truncate text-caption text-fg-3">{previewHint(item.payload)} · {new Date(item.updated_at).toLocaleString()}</div>
                </div>
                <Button type="button" variant="ghost" size="sm" onClick={() => load(item.name, item.payload, item.id, null)}>Edit</Button>
                <Button type="button" variant="ghost" size="sm" onClick={() => {
                  setChannelId("");
                  load(item.name, item.payload, item.id, null);
                  setSendOpen(true);
                }}>Send</Button>
                <Button type="button" variant="ghost" size="sm" onClick={async () => {
                  const saved = await api.createMessageTemplate(guildId, { name: `${item.name} copy`, payload: item.payload });
                  setTemplates((rows) => [saved, ...rows]);
                  toast.success("Duplicated");
                }}>Duplicate</Button>
                <Button type="button" variant="ghost" size="sm" onClick={() => download(item.name, item.payload)}>Export</Button>
                <Button type="button" variant="ghost" size="sm" onClick={async () => {
                  const next = window.prompt("Rename template", item.name);
                  if (!next || next === item.name) return;
                  const saved = await api.updateMessageTemplate(guildId, item.id, { name: next });
                  setTemplates((rows) => rows.map((row) => (row.id === saved.id ? saved : row)));
                }}>Rename</Button>
                <Button type="button" variant="danger-secondary" size="sm" onClick={async () => {
                  if (!window.confirm(`Delete ${item.name}?`)) return;
                  await api.deleteMessageTemplate(guildId, item.id);
                  setTemplates((rows) => rows.filter((row) => row.id !== item.id));
                }}>Delete</Button>
              </li>
            ))}
          </ul>
        </div>
      )}

      {tab === "editor" && (
        <div className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <Input value={name} onChange={(event) => setName(event.target.value)} aria-label="Template name" className="max-w-xs" />
            <Button type="button" variant="primary" disabled={busy} onClick={() => void save(false)}>Save</Button>
            <Button type="button" variant="secondary" disabled={busy} onClick={() => void save(true)}>Save as new</Button>
            <Button type="button" variant="secondary" disabled={busy || !templateId} onClick={() => void save(true)}>Duplicate</Button>
            <Button type="button" variant="secondary" onClick={() => download(name, message)}>Export</Button>
            <Button type="button" variant="secondary" onClick={() => setSendOpen(true)}>Send</Button>
            {sentId && <Button type="button" variant="primary" disabled={busy} onClick={() => void updateDiscord()}>Update Discord message</Button>}
            <button type="button" className={cn("h-8 rounded-sm px-2 text-caption", jsonMode ? "bg-surface-3 text-fg-1" : "text-fg-3")} onClick={() => { setJsonText(JSON.stringify(message, null, 2)); setJsonMode((value) => !value); }}>JSON</button>
            <div className="flex gap-1 lg:hidden">
              <button type="button" className={cn("h-8 rounded-sm px-2 text-caption", pane === "edit" ? "bg-surface-3 text-fg-1" : "text-fg-3")} onClick={() => setPane("edit")}>Edit</button>
              <button type="button" className={cn("h-8 rounded-sm px-2 text-caption", pane === "preview" ? "bg-surface-3 text-fg-1" : "text-fg-3")} onClick={() => setPane("preview")}>Preview</button>
            </div>
          </div>
          {errors.length > 0 && (
            <ul className="rounded-sm border border-red-400/40 bg-red-400/10 px-3 py-2 text-caption text-red-300">
              {errors.map((error) => <li key={error}>{error}</li>)}
            </ul>
          )}
          {jsonMode ? (
            <div className="space-y-2">
              <textarea value={jsonText} onChange={(event) => setJsonText(event.target.value)} className="h-80 w-full rounded-sm border border-line-input bg-surface-well p-3 font-mono text-caption text-fg-1" />
              <Button type="button" variant="secondary" onClick={() => {
                const parsed = parseMessageJson(jsonText);
                if (!parsed.message) {
                  setErrors(parsed.errors);
                  return;
                }
                changeMessage(parsed.message);
                setJsonMode(false);
              }}>Apply JSON</Button>
            </div>
          ) : (
            <>
              <div className={pane === "preview" ? "lg:hidden" : "hidden"}>
                <DiscordMessagePreview guildId={guildId} message={message} values={values} />
              </div>
              <div className={pane === "edit" ? "block" : "hidden lg:block"}>
                <MessageComposer
                  guildId={guildId}
                  message={message}
                  onChange={changeMessage}
                  emojis={emojis}
                  values={values}
                  selection={selection}
                  onSelect={setSelection}
                  showPreview
                />
              </div>
            </>
          )}
        </div>
      )}

      {tab === "sent" && (
        <div className="space-y-3">
          <div className="flex gap-2">
            <Button type="button" variant="secondary" onClick={() => void refreshSent()}>Refresh</Button>
          </div>
          {sent.length === 0 && <p className="rounded-md border border-dashed border-line px-3 py-8 text-center text-caption text-fg-3">No messages sent from CLS yet.</p>}
          <ul className="divide-y divide-line rounded-md border border-line">
            {sent.map((row) => {
              const channel = channelOptions.find((item) => item.id === row.channel_id);
              const template = templates.find((item) => item.id === row.template_id);
              return (
                <li key={row.id} className="flex flex-wrap items-center gap-2 px-3 py-2">
                  <div className="min-w-0 flex-1">
                    <div className="text-body text-fg-1">{channel ? `#${channel.name}` : "Channel"} · {previewHint(row.payload)}</div>
                    <div className="text-caption text-fg-3">
                      {template?.name || "No template"} · {new Date(row.sent_at).toLocaleString()} · {row.missing ? "Missing" : row.edited_at ? "Edited" : "Sent"}
                    </div>
                  </div>
                  <a className="text-caption text-brand-400" href={row.jump_url} target="_blank" rel="noreferrer">Open in Discord</a>
                  <Button type="button" variant="ghost" size="sm" onClick={() => load(template?.name || "Sent message", row.payload, row.template_id, row.id)}>Edit</Button>
                  {row.missing && (
                    <Button type="button" variant="secondary" size="sm" onClick={async () => {
                      const next = await api.resendSentMessage(guildId, row.id);
                      setSent((rows) => rows.map((item) => (item.id === next.id ? next : item)));
                      toast.success("Resent");
                    }}>Resend</Button>
                  )}
                  {!row.missing && (
                    <Button type="button" variant="ghost" size="sm" onClick={async () => {
                      if (!window.confirm("Delete this Discord message?")) return;
                      const next = await api.removeSentMessage(guildId, row.id);
                      setSent((rows) => rows.map((item) => (item.id === next.id ? next : item)));
                    }}>Remove from Discord</Button>
                  )}
                  <Button type="button" variant="ghost" size="sm" onClick={async () => {
                    await api.deleteSentRecord(guildId, row.id);
                    setSent((rows) => rows.filter((item) => item.id !== row.id));
                  }}>Delete record</Button>
                </li>
              );
            })}
          </ul>
        </div>
      )}

      <Dialog open={sendOpen} onOpenChange={setSendOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Send message</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-3">
            <ChannelPicker channels={channelOptions} value={channelId} onChange={setChannelId} />
            <Button type="button" variant="primary" disabled={busy || !channelId} onClick={() => void send()}>Send</Button>
          </DialogBody>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function download(name: string, message: MessageDraft) {
  const blob = new Blob([JSON.stringify(message, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = `${name.replace(/[^\w.-]+/g, "-") || "message"}.json`;
  link.click();
  URL.revokeObjectURL(url);
}
