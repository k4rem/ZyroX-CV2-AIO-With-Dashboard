"use client";

import React, { useMemo, useState } from "react";
import { toast } from "sonner";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { ChannelPicker, type ChannelOption } from "@/components/discord/channel-picker";
import { type GuildEmoji } from "@/components/discord/emoji-picker";
import { MessageComposer, type ComposerSelection } from "@/components/discord/message-composer";
import { DiscordMessagePreview } from "@/components/discord/message-preview";
import { ApiError, api } from "@/lib/api";
import { emptyMessage, validateMessage, type MessageDraft } from "@/lib/messagePayload";
import { cn } from "@/lib/utils";
import { GOODBYE_MESSAGE_VARIABLES, WELCOME_MESSAGE_VARIABLES, asMessageDraft, sameWelcomeState } from "@/lib/welcomeState";

type Mode = "welcome" | "dm" | "goodbye";

type ChannelDraft = {
  enabled: boolean;
  skipBots: boolean;
  channelId: string;
  autoDelete: string;
  payload: MessageDraft;
  channelOk: boolean;
};

type DirectDraft = { enabled: boolean; payload: MessageDraft };

function explain(err: unknown) {
  if (err instanceof ApiError) return err.message;
  return "Something went wrong";
}

function channelDraft(raw: any): ChannelDraft {
  return {
    enabled: Boolean(raw?.enabled),
    skipBots: Boolean(raw?.skip_bots),
    channelId: raw?.channel_id ? String(raw.channel_id) : "",
    autoDelete: raw?.auto_delete_duration ? String(raw.auto_delete_duration) : "",
    payload: asMessageDraft(raw?.payload),
    channelOk: raw?.channel_ok !== false,
  };
}

function directDraft(raw: any): DirectDraft {
  return { enabled: Boolean(raw?.enabled), payload: asMessageDraft(raw?.payload) };
}

export function WelcomeWorkspace({
  guildId,
  home,
  emojis,
  initialMode,
}: {
  guildId: string;
  home: any;
  emojis: GuildEmoji[];
  initialMode: Mode;
}) {
  const [mode, setMode] = useState<Mode>(initialMode);
  const [welcome, setWelcome] = useState<ChannelDraft>(() => channelDraft(home?.welcome));
  const [dm, setDm] = useState<DirectDraft>(() => directDraft(home?.dm));
  const [goodbye, setGoodbye] = useState<ChannelDraft>(() => channelDraft(home?.goodbye));
  const [saved, setSaved] = useState(() => ({
    welcome: channelDraft(home?.welcome),
    dm: directDraft(home?.dm),
    goodbye: channelDraft(home?.goodbye),
  }));
  const [selection, setSelection] = useState<ComposerSelection>({ kind: "embed", index: 0 });
  const [pane, setPane] = useState<"edit" | "preview">("edit");
  const [density, setDensity] = useState<"desktop" | "mobile">("desktop");
  const [testChannelId, setTestChannelId] = useState("");
  const [busy, setBusy] = useState(false);
  const [errors, setErrors] = useState<string[]>([]);
  const preview = (home?.preview || {}) as Record<string, string>;
  const destinations: ChannelOption[] = (home?.destinations || []).map((channel: any) => ({
    id: String(channel.id),
    name: channel.name,
    type: "0",
    parent_name: channel.parent_name || null,
  }));

  const current = mode === "welcome" ? welcome : mode === "goodbye" ? goodbye : dm;
  const dirty = useMemo(() => {
    if (mode === "dm") return !sameWelcomeState(dm, saved.dm);
    if (mode === "goodbye") return !sameWelcomeState(goodbye, saved.goodbye);
    return !sameWelcomeState(welcome, saved.welcome);
  }, [mode, welcome, dm, goodbye, saved]);

  function setPayload(next: MessageDraft) {
    if (mode === "dm") setDm({ ...dm, payload: next });
    else if (mode === "goodbye") setGoodbye({ ...goodbye, payload: next });
    else setWelcome({ ...welcome, payload: next });
  }

  function discard() {
    setWelcome(saved.welcome);
    setDm(saved.dm);
    setGoodbye(saved.goodbye);
    setErrors([]);
  }

  async function save() {
    const payload = current.payload;
    const enabled = current.enabled;
    const problems = enabled ? validateMessage(payload) : [];
    if (enabled && (mode === "welcome" || mode === "goodbye") && !(current as ChannelDraft).channelId) {
      problems.push("Choose a channel.");
    }
    if (mode === "welcome" && welcome.autoDelete.trim()) {
      const seconds = Number(welcome.autoDelete);
      if (!Number.isInteger(seconds) || seconds < 0 || seconds > 86400) problems.push("Auto-delete must be between 0 and 86400 seconds.");
    }
    setErrors(problems);
    if (problems.length) return;
    setBusy(true);
    try {
      if (mode === "dm") {
        const next = await api.saveWelcomeDm(guildId, { enabled: dm.enabled, payload: dm.payload });
        const draft = directDraft(next);
        setDm(draft);
        setSaved((value) => ({ ...value, dm: draft }));
      } else if (mode === "goodbye") {
        const next = await api.saveWelcomeGoodbye(guildId, {
          enabled: goodbye.enabled,
          skip_bots: goodbye.skipBots,
          channel_id: goodbye.channelId || null,
          payload: goodbye.payload,
        });
        const draft = channelDraft(next);
        setGoodbye(draft);
        setSaved((value) => ({ ...value, goodbye: draft }));
      } else {
        const next = await api.saveWelcomeChannel(guildId, {
          enabled: welcome.enabled,
          skip_bots: welcome.skipBots,
          channel_id: welcome.channelId || null,
          auto_delete_duration: welcome.autoDelete.trim() ? Number(welcome.autoDelete) : null,
          payload: welcome.payload,
        });
        const draft = channelDraft(next);
        setWelcome(draft);
        setSaved((value) => ({ ...value, welcome: draft }));
      }
      toast.success("Saved");
    } catch (err) {
      toast.error(explain(err));
    } finally {
      setBusy(false);
    }
  }

  async function sendTest(target: "me" | "channel") {
    const problems = validateMessage(current.payload);
    const channelId = mode === "dm" ? testChannelId : (current as ChannelDraft).channelId;
    if (target === "channel" && !channelId) problems.push("Choose a channel.");
    setErrors(problems);
    if (problems.length) return;
    setBusy(true);
    try {
      await api.sendWelcomeTest(guildId, {
        mode,
        target,
        channel_id: target === "channel" ? channelId : null,
        payload: current.payload,
      });
      toast.success(target === "me" ? "Test sent to you" : "Test sent to the channel");
    } catch (err) {
      toast.error(explain(err));
    } finally {
      setBusy(false);
    }
  }

  const channel = mode === "dm" ? null : (current as ChannelDraft);
  const variables = mode === "goodbye" ? GOODBYE_MESSAGE_VARIABLES : WELCOME_MESSAGE_VARIABLES;

  return (
    <div className="space-y-4 pb-8">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <h1 className="text-title text-fg-1">Welcome</h1>
          <p className="text-caption text-fg-3">Channel greeting, direct message, and goodbye.</p>
        </div>
        <div className="flex gap-1 rounded-sm border border-line bg-surface-2 p-1">
          {(["welcome", "dm", "goodbye"] as Mode[]).map((item) => (
            <button
              key={item}
              type="button"
              className={cn("h-8 rounded-sm px-3 text-caption", mode === item ? "bg-surface-3 text-fg-1" : "text-fg-3")}
              onClick={() => {
                setMode(item);
                setSelection({ kind: "embed", index: 0 });
                setErrors([]);
              }}
            >
              {item === "welcome" ? "Welcome" : item === "dm" ? "Direct message" : "Goodbye"}
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-3 rounded-sm border border-line bg-surface-1 p-3">
        <div className="flex flex-wrap items-center gap-3">
          <label className="flex items-center gap-2 text-caption text-fg-2">
            <Switch checked={current.enabled} onCheckedChange={(enabled) => {
              if (mode === "dm") setDm({ ...dm, enabled });
              else if (mode === "goodbye") setGoodbye({ ...goodbye, enabled });
              else setWelcome({ ...welcome, enabled });
            }} />
            {current.enabled ? "Enabled" : "Disabled"}
          </label>
          {channel && (
            <div className="min-w-[220px] flex-1">
              <ChannelPicker channels={destinations} value={channel.channelId} onChange={(channelId) => {
                if (mode === "goodbye") setGoodbye({ ...goodbye, channelId, channelOk: true });
                else setWelcome({ ...welcome, channelId, channelOk: true });
              }} />
            </div>
          )}
          {mode === "welcome" && (
            <label className="flex items-center gap-2 text-caption text-fg-3">
              Auto-delete
              <Input
                value={welcome.autoDelete}
                onChange={(event) => setWelcome({ ...welcome, autoDelete: event.target.value })}
                inputMode="numeric"
                aria-label="Auto-delete seconds"
                placeholder="seconds"
                className="w-24"
              />
            </label>
          )}
          {channel && (
            <label className="flex items-center gap-2 text-caption text-fg-2">
              <Switch checked={channel.skipBots} onCheckedChange={(skipBots) => {
                if (mode === "goodbye") setGoodbye({ ...goodbye, skipBots });
                else setWelcome({ ...welcome, skipBots });
              }} />
              Skip bots
            </label>
          )}
          <div className="ml-auto flex flex-wrap items-center gap-2">
            {dirty && <span className="text-caption text-amber-300">Unsaved changes</span>}
            <Button type="button" variant="ghost" disabled={!dirty || busy} onClick={discard}>Discard</Button>
            <Button type="button" variant="primary" disabled={busy} onClick={() => void save()}>Save</Button>
            <Button type="button" variant="secondary" disabled={busy} onClick={() => void sendTest("me")}>Send test to me</Button>
            <Button type="button" variant="secondary" disabled={busy} onClick={() => void sendTest("channel")}>Send test to channel</Button>
          </div>
        </div>
        {mode === "dm" && (
          <div className="max-w-sm">
            <div className="mb-1 text-caption text-fg-3">Channel for “Send test to channel”</div>
            <ChannelPicker channels={destinations} value={testChannelId} onChange={setTestChannelId} />
          </div>
        )}
        {channel && channel.channelId && !channel.channelOk && (
          <p className="text-caption text-amber-300">CLS cannot send embeds in the saved channel. Choose another destination.</p>
        )}
        {destinations.length === 0 && <p className="text-caption text-fg-3">No text channels where CLS can send embeds.</p>}
      </div>

      {errors.length > 0 && (
        <ul className="rounded-sm border border-red-400/40 bg-red-400/10 px-3 py-2 text-caption text-red-300">
          {errors.map((error) => <li key={error}>{error}</li>)}
        </ul>
      )}

      <div className="flex flex-wrap items-center gap-2 lg:justify-end">
        <div className="flex gap-1 lg:hidden">
          <button type="button" className={cn("h-8 rounded-sm px-2 text-caption", pane === "edit" ? "bg-surface-3 text-fg-1" : "text-fg-3")} onClick={() => setPane("edit")}>Edit</button>
          <button type="button" className={cn("h-8 rounded-sm px-2 text-caption", pane === "preview" ? "bg-surface-3 text-fg-1" : "text-fg-3")} onClick={() => setPane("preview")}>Preview</button>
        </div>
        <div className="hidden gap-1 lg:flex">
          <button type="button" className={cn("h-8 rounded-sm px-2 text-caption", density === "desktop" ? "bg-surface-3 text-fg-1" : "text-fg-3")} onClick={() => setDensity("desktop")}>Desktop</button>
          <button type="button" className={cn("h-8 rounded-sm px-2 text-caption", density === "mobile" ? "bg-surface-3 text-fg-1" : "text-fg-3")} onClick={() => setDensity("mobile")}>Mobile</button>
        </div>
      </div>

      <div className={pane === "preview" ? "lg:hidden" : "hidden"}>
        <DiscordMessagePreview guildId={guildId} message={current.payload || emptyMessage()} values={preview} />
      </div>
      <div className={pane === "edit" ? "block" : "hidden lg:block"}>
        <MessageComposer
          guildId={guildId}
          message={current.payload}
          onChange={setPayload}
          emojis={emojis}
          values={preview}
          variables={variables}
          selection={selection}
          onSelect={setSelection}
          showPreview
          previewDensity={density}
        />
      </div>
    </div>
  );
}
