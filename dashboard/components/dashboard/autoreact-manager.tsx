"use client";

import React, { useCallback, useEffect, useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { ChannelPicker, type ChannelOption } from "@/components/discord/channel-picker";
import { EmojiPicker, type GuildEmoji } from "@/components/discord/emoji-picker";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { StatusLabel } from "@/components/ui/status";
import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api";
import { emptyRule, triggerSummary, type AutoReactRule } from "@/lib/autoreact";

const MODES = [
  { value: "contains", label: "Contains" },
  { value: "exact", label: "Exact" },
  { value: "starts", label: "Starts with" },
  { value: "ends", label: "Ends with" },
];

const SCOPES = [
  { value: "all", label: "All channels" },
  { value: "selected", label: "Selected channels" },
  { value: "excluded", label: "Excluded channels" },
];

function emojiLabel(token: string) {
  const match = token.match(/^<a?:([^:]+):\d+>$/);
  return match ? `:${match[1]}:` : token;
}

export function AutoReactManager({ guildId }: { guildId: string }) {
  const [rules, setRules] = useState<AutoReactRule[]>([]);
  const [channels, setChannels] = useState<ChannelOption[]>([]);
  const [emojis, setEmojis] = useState<GuildEmoji[]>([]);
  const [draft, setDraft] = useState<AutoReactRule | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const body = await api.getAutoReactRules(guildId);
    setRules(body?.rules ?? []);
  }, [guildId]);

  useEffect(() => {
    void load().catch(() => setRules([]));
    api.getChannels(guildId).then((body) => setChannels(Array.isArray(body) ? body : [])).catch(() => setChannels([]));
    api.listGuildEmojis(guildId).then((body) => setEmojis(body?.emojis ?? [])).catch(() => setEmojis([]));
  }, [guildId, load]);

  const channelName = (id: string) => channels.find((channel) => channel.id === id)?.name || "Unknown channel";

  async function save(next: Omit<AutoReactRule, "health">) {
    if (!next.name.trim() || !next.pattern.trim() || next.emojis.length === 0) {
      toast.error("Name, match text, and at least one emoji are required");
      return;
    }
    setBusy(true);
    try {
      if (next.id) await api.updateAutoReactRule(guildId, next.id, next);
      else await api.createAutoReactRule(guildId, next);
      setDraft(null);
      await load();
      toast.success("Rule saved");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not save the rule");
    } finally {
      setBusy(false);
    }
  }

  async function act(kind: "duplicate" | "delete" | "toggle", rule: AutoReactRule) {
    setBusy(true);
    try {
      if (kind === "duplicate") await api.duplicateAutoReactRule(guildId, rule.id);
      if (kind === "delete") await api.deleteAutoReactRule(guildId, rule.id);
      if (kind === "toggle") await api.updateAutoReactRule(guildId, rule.id, { ...rule, enabled: !rule.enabled });
      await load();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not update the rule");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader title="Auto react" description="React to member messages that match a rule. Bot messages are ignored." />
      <div className="flex justify-end">
        <Button type="button" onClick={() => setDraft({ id: "", health: "Needs text", ...emptyRule() })}>New rule</Button>
      </div>
      {rules.length === 0 ? <p className="border border-line-subtle px-3 py-4 text-small text-fg-3">No reaction rules yet.</p> : (
        <ul className="divide-y divide-line-subtle border border-line-subtle">
          {rules.map((rule) => (
            <li key={rule.id} className="grid grid-cols-1 gap-2 px-3 py-2 md:grid-cols-[minmax(0,1fr)_auto] md:items-center">
              <div className="min-w-0">
                <p className="truncate text-small text-fg-1">{rule.name}</p>
                <p className="truncate text-caption text-fg-3">{triggerSummary(rule)} · {rule.scope === "all" ? "All channels" : `${rule.channel_ids.length} channels`} · {rule.emojis.map(emojiLabel).join(" ")}</p>
              </div>
              <div className="flex flex-wrap items-center gap-2">
                <StatusLabel status={rule.health === "Ready" ? "healthy" : rule.enabled ? "warning" : "disabled"}>{rule.health}</StatusLabel>
                <Button type="button" variant="ghost" disabled={busy} onClick={() => setDraft(rule)}>Edit</Button>
                <Button type="button" variant="ghost" disabled={busy} onClick={() => void act("duplicate", rule)}>Duplicate</Button>
                <Button type="button" variant="ghost" disabled={busy} onClick={() => void act("toggle", rule)}>{rule.enabled ? "Disable" : "Enable"}</Button>
                <Button type="button" variant="danger-secondary" disabled={busy} onClick={() => void act("delete", rule)}>Delete</Button>
              </div>
            </li>
          ))}
        </ul>
      )}
      {draft ? (
        <form className="space-y-3 border border-line bg-surface-1 p-3" onSubmit={(event) => { event.preventDefault(); void save(draft); }}>
          <Input value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} placeholder="Rule name" aria-label="Rule name" />
          <label className="flex items-center justify-between text-small text-fg-1">
            Enabled
            <Switch checked={draft.enabled} onCheckedChange={(value) => setDraft({ ...draft, enabled: value })} aria-label="Rule enabled" />
          </label>
          <Select value={draft.scope} onValueChange={(value) => setDraft({ ...draft, scope: value as AutoReactRule["scope"] })} options={SCOPES} />
          {draft.scope !== "all" ? (
            <div className="space-y-2">
              <ChannelPicker channels={channels} value="" onChange={(id) => setDraft({ ...draft, channel_ids: draft.channel_ids.includes(id) ? draft.channel_ids : [...draft.channel_ids, id] })} />
              <div className="flex flex-wrap gap-2">
                {draft.channel_ids.map((id) => (
                  <button key={id} type="button" className="text-caption text-fg-2" onClick={() => setDraft({ ...draft, channel_ids: draft.channel_ids.filter((item) => item !== id) })}>#{channelName(id)} · remove</button>
                ))}
              </div>
            </div>
          ) : null}
          <Select value={draft.mode} onValueChange={(value) => setDraft({ ...draft, mode: value as AutoReactRule["mode"] })} options={MODES} />
          <Input value={draft.pattern} onChange={(event) => setDraft({ ...draft, pattern: event.target.value })} placeholder="Match text" aria-label="Match text" />
          <div className="flex flex-wrap items-center gap-2">
            {draft.emojis.map((emoji) => (
              <button key={emoji} type="button" className="text-body" onClick={() => setDraft({ ...draft, emojis: draft.emojis.filter((item) => item !== emoji) })}>{emojiLabel(emoji)}</button>
            ))}
            <EmojiPicker value="" emojis={emojis} onChange={(emoji) => emoji && setDraft({ ...draft, emojis: draft.emojis.includes(emoji) ? draft.emojis : [...draft.emojis, emoji] })} />
          </div>
          <div className="flex gap-2">
            <Button type="submit" disabled={busy}>Save</Button>
            <Button type="button" variant="ghost" onClick={() => setDraft(null)}>Cancel</Button>
          </div>
        </form>
      ) : null}
    </div>
  );
}
