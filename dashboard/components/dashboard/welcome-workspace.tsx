"use client";

import { useEffect, useMemo, useRef, useState, type FocusEvent } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { DiscordPreview } from "@/components/discord/discord-preview";
import { ModuleLinks } from "@/components/settings/module-links";
import { SaveBar } from "@/components/settings/save-bar";
import { SettingGroup } from "@/components/settings/setting-group";
import { SettingRow } from "@/components/settings/setting-row";
import { useDraft } from "@/components/settings/use-draft";
import { StatusLabel } from "@/components/ui/status";
import { Button } from "@/components/ui/button";
import { Combobox, type ComboboxOption } from "@/components/ui/combobox";
import { Input } from "@/components/ui/input";
import { Segmented } from "@/components/ui/segmented";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { api } from "@/lib/api";
import {
  WELCOME_VARIABLES,
  defaultWelcomeEmbed,
  interpretWelcomeColor,
  previewClock,
  safeHttpUrl,
  substituteWelcome,
  welcomeDraftFromApi,
  welcomeUpdatePayload,
  welcomeValueMap,
  type WelcomeDraft,
  type WelcomePreviewContext,
} from "@/lib/welcomeFormat";
import type { DiscordChannel } from "@/types/api";

function channelGlyph(type: string): ComboboxOption["glyph"] {
  if (type === "2") return "voice";
  if (type === "4") return "category";
  if (type === "5") return "announce";
  if (type === "13") return "stage";
  return "text";
}

export function WelcomeWorkspace({
  guildId,
  initialConfig,
  channels,
  guildName,
  guildIcon,
  memberCount,
  serverId,
  botName,
  botAvatar,
  viewer,
}: {
  guildId: string;
  initialConfig: Parameters<typeof welcomeDraftFromApi>[0];
  channels: DiscordChannel[];
  guildName: string | null;
  guildIcon: string | null;
  memberCount: number | null;
  serverId: string | null;
  botName: string;
  botAvatar: string | null;
  viewer: { id: string | null; name: string | null; image: string | null };
}) {
  const { draft, setDraft, dirty, reset, commit } = useDraft<WelcomeDraft>(welcomeDraftFromApi(initialConfig));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [pane, setPane] = useState<"edit" | "preview">("edit");
  const [frame, setFrame] = useState<"desktop" | "mobile">("desktop");
  const [width, setWidth] = useState(0);
  const [clock, setClock] = useState<string | null>(null);
  const rootRef = useRef<HTMLDivElement>(null);
  const fieldRef = useRef<{ get: () => string; set: (value: string) => void; el: HTMLTextAreaElement | HTMLInputElement | null } | null>(null);

  useEffect(() => {
    const node = rootRef.current?.parentElement ?? rootRef.current;
    if (!node) return;
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    observer.observe(node);
    return () => observer.disconnect();
  }, []);
  useEffect(() => {
    setClock(`today at ${previewClock()}`);
  }, []);

  const stacked = width < 1024;
  const textChannels = channels.filter((channel) => channel.type === "0" || channel.type === "5");
  const channelOptions: ComboboxOption[] = textChannels.map((channel) => ({
    value: channel.id,
    label: channel.name,
    glyph: channelGlyph(channel.type),
  }));
  const channel = textChannels.find((item) => item.id === draft.channel_id);
  const color = interpretWelcomeColor(draft.embed.color);
  const hasBody =
    draft.welcome_type === "simple"
      ? draft.welcome_message.trim().length > 0
      : Boolean(draft.embed.message.trim() || draft.embed.title.trim() || draft.embed.description.trim());
  const active = Boolean(draft.channel_id) && hasBody;

  const context: WelcomePreviewContext = {
    userId: viewer.id,
    userName: viewer.name,
    userAvatar: viewer.image,
    userNick: viewer.name,
    userJoinDate: null,
    userCreateDate: null,
    serverName: guildName,
    serverId,
    serverMemberCount: memberCount,
    serverIcon: guildIcon,
    timestamp: clock,
  };
  const values = welcomeValueMap(context);
  const source =
    draft.welcome_type === "simple"
      ? draft.welcome_message
      : [draft.embed.message, draft.embed.title, draft.embed.description, draft.embed.author_name, draft.embed.footer_text]
          .filter(Boolean)
          .join("\n");
  const resolved = substituteWelcome(source, values);
  const warn = [...resolved.unknown, ...resolved.unresolved];
  const content = substituteWelcome(draft.welcome_type === "embed" ? draft.embed.message : draft.welcome_message, values);
  const title = substituteWelcome(draft.embed.title, values);
  const description = substituteWelcome(draft.embed.description, values);
  const author = substituteWelcome(draft.embed.author_name, values);
  const footer = substituteWelcome(draft.embed.footer_text, values);
  const media = (raw: string) => safeHttpUrl(substituteWelcome(raw, values).text);

  const bind = (set: (value: string) => void) => ({
    onFocus: (event: FocusEvent<HTMLTextAreaElement | HTMLInputElement>) => {
      const el = event.currentTarget;
      fieldRef.current = { el, get: () => el.value, set };
    },
  });

  const insert = (key: string) => {
    const token = `{${key}}`;
    const field = fieldRef.current;
    if (!field?.el) {
      setDraft((current) => ({ ...current, welcome_message: `${current.welcome_message}${token}` }));
      return;
    }
    const el = field.el;
    const start = el.selectionStart ?? el.value.length;
    const end = el.selectionEnd ?? start;
    field.set(`${el.value.slice(0, start)}${token}${el.value.slice(end)}`);
  };

  const save = async () => {
    if (!color.valid) {
      setError(color.error);
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.updateWelcome(guildId, welcomeUpdatePayload(draft));
      commit(draft);
      toast.success("Welcome settings saved");
    } catch {
      setError("Could not save welcome settings.");
      toast.error("Could not save welcome settings");
    } finally {
      setSaving(false);
    }
  };

  const composer = (
    <div className="min-w-0">
      <div className="border border-line bg-surface-1 px-3 py-2">
        <p className="text-small text-fg-1" dir="auto">
          {channel ? `Sends to #${channel.name} when a member joins` : "Not sending until a channel and a message are set"}
        </p>
        <div className="mt-1 flex flex-wrap items-center gap-3">
          <StatusLabel status={active ? "online" : "disabled"}>{active ? "Active" : "Not sending"}</StatusLabel>
          {draft.auto_delete_duration ? (
            <span className="font-mono text-caption text-fg-3">Deletes after {draft.auto_delete_duration}s</span>
          ) : null}
        </div>
      </div>

      <SettingGroup id="welcome-delivery" label="Delivery">
        <SettingRow label="Channel" description="Text or announcement channel." htmlFor="welcome-channel">
          <Combobox
            id="welcome-channel"
            value={draft.channel_id}
            onValueChange={(value) => setDraft({ ...draft, channel_id: value })}
            options={channelOptions}
            placeholder="Select a channel"
            searchLabel="Search channels"
          />
        </SettingRow>
        <SettingRow label="Format" description="Plain text, or a Discord embed.">
          <Segmented
            label="Message format"
            value={draft.welcome_type}
            onChange={(value) => setDraft({ ...draft, welcome_type: value })}
            options={[
              { value: "simple", label: "Text" },
              { value: "embed", label: "Embed" },
            ]}
          />
        </SettingRow>
      </SettingGroup>

      {draft.welcome_type === "simple" ? (
        <SettingGroup id="welcome-message" label="Message" meta={`${draft.welcome_message.length}/2000`}>
          <div className="px-3 pt-3">
            <textarea
              value={draft.welcome_message}
              maxLength={2000}
              onChange={(event) => setDraft({ ...draft, welcome_message: event.target.value })}
              {...bind((value) => setDraft((current) => ({ ...current, welcome_message: value })))}
              placeholder="Welcome {user} to {server_name}!"
              className="min-h-32 w-full rounded-sm border border-line-input bg-surface-well p-2 text-body text-fg-1 outline-none focus-visible:border-brand-400"
            />
          </div>
        </SettingGroup>
      ) : (
        <>
          <SettingGroup id="welcome-content" label="Content" meta={`${draft.embed.description.length}/4096`}>
            <div className="space-y-3 px-3 pt-3">
              <label className="block text-small text-fg-2">
                Message above the embed
                <textarea
                  value={draft.embed.message}
                  maxLength={2000}
                  onChange={(event) => setDraft({ ...draft, embed: { ...draft.embed, message: event.target.value } })}
                  {...bind((value) => setDraft((current) => ({ ...current, embed: { ...current.embed, message: value } })))}
                  className="mt-1 min-h-16 w-full rounded-sm border border-line-input bg-surface-well p-2 text-body text-fg-1 outline-none focus-visible:border-brand-400"
                />
              </label>
              <label className="block text-small text-fg-2">
                Title
                <Input
                  value={draft.embed.title}
                  onChange={(event) => setDraft({ ...draft, embed: { ...draft.embed, title: event.target.value } })}
                  {...bind((value) => setDraft((current) => ({ ...current, embed: { ...current.embed, title: value } })))}
                  className="mt-1"
                />
              </label>
              <label className="block text-small text-fg-2">
                Description
                <textarea
                  value={draft.embed.description}
                  maxLength={4096}
                  onChange={(event) => setDraft({ ...draft, embed: { ...draft.embed, description: event.target.value } })}
                  {...bind((value) => setDraft((current) => ({ ...current, embed: { ...current.embed, description: value } })))}
                  className="mt-1 min-h-24 w-full rounded-sm border border-line-input bg-surface-well p-2 text-body text-fg-1 outline-none focus-visible:border-brand-400"
                />
              </label>
            </div>
          </SettingGroup>
          <details className="mt-4">
            <summary className="cursor-pointer text-small text-fg-2">Appearance, author, media, footer</summary>
            <div className="mt-3 space-y-3 px-3">
              <label className="block text-small text-fg-2">
                Colour
                <span className="mt-1 flex items-center gap-2">
                  <span className="size-4 shrink-0 border border-line" style={{ background: color.preview }} />
                  <Input
                    value={draft.embed.color}
                    aria-invalid={!color.valid}
                    placeholder="#2F3136"
                    onChange={(event) => setDraft({ ...draft, embed: { ...draft.embed, color: event.target.value } })}
                  />
                </span>
              </label>
              {!color.valid ? <p className="text-small text-warn">{color.error}</p> : null}
              <Pair
                label="Author name"
                value={draft.embed.author_name}
                onChange={(value) => setDraft({ ...draft, embed: { ...draft.embed, author_name: value } })}
              />
              <Pair
                label="Author icon URL"
                value={draft.embed.author_icon}
                onChange={(value) => setDraft({ ...draft, embed: { ...draft.embed, author_icon: value } })}
              />
              <Pair
                label="Thumbnail"
                value={draft.embed.thumbnail}
                onChange={(value) => setDraft({ ...draft, embed: { ...draft.embed, thumbnail: value } })}
              />
              <Pair
                label="Image"
                value={draft.embed.image}
                onChange={(value) => setDraft({ ...draft, embed: { ...draft.embed, image: value } })}
              />
              <Pair
                label="Footer"
                value={draft.embed.footer_text}
                onChange={(value) => setDraft({ ...draft, embed: { ...draft.embed, footer_text: value } })}
              />
              <Pair
                label="Footer icon URL"
                value={draft.embed.footer_icon}
                onChange={(value) => setDraft({ ...draft, embed: { ...draft.embed, footer_icon: value } })}
              />
            </div>
          </details>
        </>
      )}

      <SettingGroup id="welcome-delete" label="Auto-delete">
        <SettingRow label="Remove after" description="Leave empty to keep the message." htmlFor="welcome-delete-seconds">
          <span className="flex items-center gap-2">
            <Input
              id="welcome-delete-seconds"
              inputMode="numeric"
              value={draft.auto_delete_duration ?? ""}
              onChange={(event) => {
                const raw = event.target.value.trim();
                if (!raw) {
                  setDraft({ ...draft, auto_delete_duration: null });
                  return;
                }
                const next = Number(raw);
                if (Number.isInteger(next) && next >= 0) setDraft({ ...draft, auto_delete_duration: next || null });
              }}
            />
            <span className="text-small text-fg-3">seconds</span>
          </span>
        </SettingRow>
      </SettingGroup>

      {warn.length > 0 ? (
        <p className="mt-3 text-small text-warn" dir="auto">
          {resolved.unknown.length ? `Unknown variable ${resolved.unknown.map((token) => `{${token}}`).join(", ")}. ` : ""}
          {resolved.unresolved.length ? "Some variables have no preview value yet, so they stay as written." : ""}
        </p>
      ) : null}

      <div className="mt-4 flex flex-wrap items-center gap-2">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button type="button" variant="secondary">
              Insert variable
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent className="max-h-80 overflow-y-auto">
            {WELCOME_VARIABLES.map((variable) => (
              <DropdownMenuItem key={variable.key} onSelect={() => insert(variable.key)}>
                <span className="font-mono text-fg-1">{`{${variable.key}}`}</span>
                <span className="ms-auto max-w-[10rem] truncate font-mono text-caption text-fg-3">
                  {values[variable.key] ?? "not available"}
                </span>
              </DropdownMenuItem>
            ))}
          </DropdownMenuContent>
        </DropdownMenu>
        <Button
          type="button"
          variant="ghost"
          onClick={() => setDraft({ ...draft, welcome_type: "embed", embed: defaultWelcomeEmbed() })}
        >
          Start from default
        </Button>
      </div>
    </div>
  );

  const stage = (
    <DiscordPreview
      mode="channel"
      channelName={channel?.name}
      botName={botName}
      botAvatar={botAvatar}
      content={content.text}
      warnTokens={[...content.unknown, ...content.unresolved, ...title.unknown, ...description.unknown]}
      width={stacked ? "mobile" : frame}
      note="Previewing as you. Join date and account age are not available in this session, so those tokens stay written out."
      embed={
        draft.welcome_type === "embed"
          ? {
              title: title.text,
              description: description.text,
              color: color.preview,
              authorName: author.text,
              authorIcon: media(draft.embed.author_icon),
              footerText: footer.text,
              footerIcon: media(draft.embed.footer_icon),
              thumbnail: media(draft.embed.thumbnail),
              image: media(draft.embed.image),
            }
          : null
      }
    />
  );

  const frameToggle = useMemo(
    () => (
      <Segmented
        label="Preview width"
        value={frame}
        onChange={setFrame}
        options={[
          { value: "desktop", label: "Desktop" },
          { value: "mobile", label: "Mobile" },
        ]}
      />
    ),
    [frame],
  );

  return (
    <div ref={rootRef} className="w-full min-w-0">
      <PageHeader
        title="Welcome"
        description="The message this server sends when a member joins."
      >
        {dirty ? <span className="text-small text-fg-2">Unsaved</span> : null}
        {!stacked ? frameToggle : null}
      </PageHeader>
      <ModuleLinks
        label="Welcome"
        links={[
          { href: `/dashboard/guild/${guildId}/welcome`, label: "Channel message", current: true },
          { href: `/dashboard/guild/${guildId}/joindm`, label: "Direct message" },
        ]}
      />
      {stacked ? (
        <div className="mb-4">
          <Segmented
            label="Editor pane"
            value={pane}
            onChange={setPane}
            options={[
              { value: "edit", label: "Edit" },
              { value: "preview", label: "Preview" },
            ]}
          />
        </div>
      ) : null}
      <div className={stacked ? "" : "grid grid-cols-[minmax(280px,480px)_minmax(0,1fr)] items-start gap-6 4xl:grid-cols-[minmax(320px,560px)_minmax(0,1fr)]"}>
        {(!stacked || pane === "edit") && composer}
        {(!stacked || pane === "preview") && <div className="border border-line-subtle">{stage}</div>}
      </div>
      <SaveBar dirty={dirty} saving={saving} error={error} onSave={() => void save()} onDiscard={reset} />
    </div>
  );
}

function Pair({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="block text-small text-fg-2">
      {label}
      <Input value={value} onChange={(event) => onChange(event.target.value)} className="mt-1" />
    </label>
  );
}
