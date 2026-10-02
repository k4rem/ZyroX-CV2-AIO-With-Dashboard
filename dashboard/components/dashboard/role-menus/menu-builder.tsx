"use client";

import { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { MENU_MODES, MENU_TYPES, menuModeLabel, menuTypeLabel } from "@/lib/roleMenuModel";
import { emptyMessage, type MessageDraft } from "@/lib/messagePayload";
import { asMessageDraft } from "@/lib/welcomeState";
import { PageHeader } from "@/components/dashboard/page-header";
import { ChannelPicker, RolePicker, type ChannelOption } from "@/components/discord/channel-picker";
import { EmojiPicker, type GuildEmoji } from "@/components/discord/emoji-picker";
import { MessageComposer, type ComposerSelection } from "@/components/discord/message-composer";
import { DiscordMessagePreview } from "@/components/discord/message-preview";
import { MessagePicker } from "@/components/discord/message-picker";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";

type Option = { role_id: string; emoji: string; label: string; description: string };
type RoleOption = { id: string; name: string; color?: number; position?: number };

function explain(err: unknown) {
  return err instanceof Error ? err.message : "The menu did not save.";
}

function swatch(color?: number) {
  if (!color) return "transparent";
  return `#${color.toString(16).padStart(6, "0")}`;
}

export function MenuBuilder({
  guildId,
  menu,
  roles,
  channels,
  emojis,
  botPosition,
}: {
  guildId: string;
  menu: Record<string, any> | null;
  roles: RoleOption[];
  channels: ChannelOption[];
  emojis: GuildEmoji[];
  botPosition: number;
}) {
  const router = useRouter();
  const [source, setSource] = useState(menu?.source || "");
  const [name, setName] = useState(menu?.name || "Pick your color");
  const [type, setType] = useState(menu?.type || "reaction");
  const [mode, setMode] = useState(menu?.mode || "unique");
  const [maxRoles, setMaxRoles] = useState(menu?.max_roles ? String(menu.max_roles) : "");
  const [channelId, setChannelId] = useState(String(menu?.channel_id || ""));
  const [messageId, setMessageId] = useState(String(menu?.message_id || ""));
  const [excerpt, setExcerpt] = useState("");
  const [message, setMessage] = useState<MessageDraft>(menu?.payload ? asMessageDraft(menu.payload) : { ...emptyMessage(), content: "", embeds: [{ ...emptyMessage().embeds[0], title: menu?.name || "Pick your color", description: "Choose a role." }] });
  const [selection, setSelection] = useState<ComposerSelection>({ kind: "embed", index: 0 });
  const [options, setOptions] = useState<Option[]>(menu?.options?.length ? menu.options.map((item: Option) => ({ role_id: item.role_id, emoji: item.emoji, label: item.label, description: item.description })) : [{ role_id: "", emoji: "🔴", label: "Red", description: "" }]);
  const [busy, setBusy] = useState(false);
  const existing = source === "existing";
  const effectiveType = existing ? "reaction" : type;
  const roleName = (id: string) => roles.find((role) => role.id === id);

  const body = useMemo(() => ({
    name,
    source: source || "created",
    type: effectiveType,
    mode,
    channel_id: channelId || null,
    max_roles: mode === "unique" || maxRoles === "" ? null : Number(maxRoles),
    payload: existing ? null : message,
    options,
  }), [name, source, effectiveType, mode, channelId, maxRoles, message, options, existing]);

  function move(index: number, direction: -1 | 1) {
    const next = options.slice();
    const target = index + direction;
    if (target < 0 || target >= next.length) return;
    const [item] = next.splice(index, 1);
    next.splice(target, 0, item);
    setOptions(next);
  }

  async function persist(publish: boolean) {
    if (!source) return;
    setBusy(true);
    try {
      const saved = menu?.id ? await api.updateRoleMenu(guildId, menu.id, body) : await api.createRoleMenu(guildId, body);
      const id = saved.id || menu?.id;
      if (publish) {
        await api.publishRoleMenu(guildId, id, { channel_id: channelId || null, message_id: existing ? messageId || null : null });
        toast.success(menu?.message_id ? "Menu updated" : "Published to Discord");
      } else {
        toast.success("Draft saved");
      }
      router.push(`/dashboard/guild/${guildId}/reactionroles/${id}`);
      router.refresh();
    } catch (err) {
      toast.error(explain(err));
    } finally {
      setBusy(false);
    }
  }

  if (!source) {
    return (
      <div>
        <PageHeader title="New role menu" description="CLS can post a new message, or attach reactions to one that already exists." />
        <div className="grid gap-2 sm:grid-cols-2">
          <button type="button" className="border border-line-subtle px-3 py-4 text-left hover:border-accent" onClick={() => setSource("created")}>
            <span className="block text-small text-fg-1">Create new message</span>
            <span className="text-caption text-fg-3">Reactions, buttons, or a select menu on a message CLS posts.</span>
          </button>
          <button type="button" className="border border-line-subtle px-3 py-4 text-left hover:border-accent" onClick={() => { setSource("existing"); setType("reaction"); }}>
            <span className="block text-small text-fg-1">Use existing message</span>
            <span className="text-caption text-fg-3">Reactions only. CLS cannot add buttons to a message it did not post.</span>
          </button>
        </div>
      </div>
    );
  }

  return (
    <div>
      <PageHeader title={name || "Role menu"} description={existing ? "Existing messages can use reactions only." : "Save keeps the draft. Publish sends it to Discord."}>
        <Button type="button" variant="secondary" disabled={busy} onClick={() => void persist(false)}>Save</Button>
        <Button type="button" disabled={busy || !channelId || (existing && !messageId)} onClick={() => void persist(true)}>{menu?.message_id ? "Update" : "Publish"}</Button>
        {menu?.status === "Message missing" && menu?.source === "created" && <Button type="button" variant="ghost" disabled={busy} onClick={() => void api.republishRoleMenu(guildId, menu.id).then(() => router.refresh())}>Republish</Button>}
      </PageHeader>
      <p className="mb-3 text-small text-fg-3">{menu?.status || "Draft"}{menu?.warnings?.[0] ? ` · ${menu.warnings[0]}` : ""}</p>
      <div className="grid items-start gap-3 xl:grid-cols-[18rem_minmax(0,1fr)_20rem]">
        <aside className="space-y-3 border border-line-subtle p-3">
          <Input value={name} aria-label="Menu name" onChange={(event) => setName(event.target.value)} />
          {!existing && <Select value={effectiveType} onValueChange={setType} options={MENU_TYPES.map((item) => ({ value: item.value, label: item.label }))} />}
          <Select value={mode} onValueChange={setMode} options={MENU_MODES.map((item) => ({ value: item.value, label: item.label }))} />
          <p className="text-caption text-fg-3">{MENU_MODES.find((item) => item.value === mode)?.hint}</p>
          {mode !== "unique" && <Input value={maxRoles} aria-label="Maximum roles" placeholder="Max roles, optional" onChange={(event) => setMaxRoles(event.target.value)} />}
          <ChannelPicker channels={channels} value={channelId} onChange={setChannelId} />
          {existing && <MessagePicker guildId={guildId} channelId={channelId} value={messageId} onChange={(item) => { setMessageId(item.id); setExcerpt(item.excerpt); setChannelId(item.channel_id || channelId); }} />}
          {existing && excerpt && <p className="text-caption text-fg-3">{excerpt}</p>}
          <div className="flex items-center justify-between">
            <p className="text-caption text-fg-3">Options</p>
            <Button type="button" size="sm" variant="ghost" disabled={options.length >= (effectiveType === "reaction" ? 20 : 25)} onClick={() => setOptions([...options, { role_id: "", emoji: "", label: "Role", description: "" }])}>Add</Button>
          </div>
          {options.map((option, index) => {
            const role = roleName(option.role_id);
            const low = role && typeof role.position === "number" && role.position >= botPosition;
            return (
              <div key={`${index}-${option.role_id}`} className="space-y-1 border border-line-subtle p-2">
                <div className="flex items-center gap-2">
                  <EmojiPicker value={option.emoji} emojis={emojis} onChange={(emoji) => setOptions(options.map((item, itemIndex) => itemIndex === index ? { ...item, emoji } : item))} />
                  <Input value={option.label} aria-label={`Option label ${index + 1}`} onChange={(event) => setOptions(options.map((item, itemIndex) => itemIndex === index ? { ...item, label: event.target.value } : item))} />
                </div>
                <RolePicker roles={roles} value={option.role_id} onChange={(role_id) => setOptions(options.map((item, itemIndex) => itemIndex === index ? { ...item, role_id, label: item.label || roles.find((role) => role.id === role_id)?.name || item.label } : item))} />
                {role && <p className="flex items-center gap-2 text-caption text-fg-3"><span className="size-2 rounded-full" style={{ background: swatch(role.color) }} />{role.name}{low ? " · above CLS" : ""}</p>}
                {effectiveType === "select" && <Input value={option.description} aria-label={`Option description ${index + 1}`} placeholder="Description" onChange={(event) => setOptions(options.map((item, itemIndex) => itemIndex === index ? { ...item, description: event.target.value } : item))} />}
                <div className="flex gap-2 text-caption">
                  <button type="button" onClick={() => move(index, -1)}>Up</button>
                  <button type="button" onClick={() => move(index, 1)}>Down</button>
                  <button type="button" onClick={() => setOptions(options.filter((_, itemIndex) => itemIndex !== index))}>Delete</button>
                </div>
              </div>
            );
          })}
        </aside>
        {!existing ? (
          <MessageComposer guildId={guildId} message={message} onChange={setMessage} emojis={emojis} values={{}} selection={selection} onSelect={setSelection} showPreview={false} />
        ) : (
          <p className="border border-line-subtle p-3 text-small text-fg-3">This menu uses the message you selected. CLS will add the reactions and will not change the message text.</p>
        )}
        <aside className="sticky top-3 border border-line-subtle p-3">
          <p className="mb-2 text-caption uppercase tracking-wide text-fg-3">Preview · {menuTypeLabel(effectiveType)} · {menuModeLabel(mode)}</p>
          {!existing && <DiscordMessagePreview guildId={guildId} message={message} values={{}} />}
          {existing && <p className="text-small text-fg-2">{excerpt || "Choose a message to see it here."}</p>}
          {effectiveType === "reaction" && <p className="mt-2 text-small text-fg-1">{options.map((option) => option.emoji || "•").join("  ")}</p>}
          {effectiveType === "button" && <div className="mt-2 flex flex-wrap gap-1">{options.map((option, index) => <span key={index} className="border border-line-subtle px-2 py-1 text-caption text-fg-1">{option.emoji} {option.label || "Role"}</span>)}</div>}
          {effectiveType === "select" && <div className="mt-2 border border-line-subtle px-2 py-1 text-small text-fg-2">{options[0] ? `${options[0].emoji} ${options[0].label}` : "Choose a role"}</div>}
        </aside>
      </div>
    </div>
  );
}
