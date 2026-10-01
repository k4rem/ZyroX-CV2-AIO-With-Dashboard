"use client";

import { useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { DiscordPreview } from "@/components/discord/discord-preview";
import { SaveBar } from "@/components/settings/save-bar";
import { SettingGroup } from "@/components/settings/setting-group";
import { SettingRow } from "@/components/settings/setting-row";
import { useDraft } from "@/components/settings/use-draft";
import { Button } from "@/components/ui/button";
import { Combobox, type ComboboxOption } from "@/components/ui/combobox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Segmented } from "@/components/ui/segmented";
import { api } from "@/lib/api";
import { roleSwatch } from "@/lib/modulePayloads";
import type { DiscordChannel, DiscordRole, TicketCategory, TicketConfig } from "@/types/api";

function channelOptions(channels: DiscordChannel[], types: string[]): ComboboxOption[] {
  return channels
    .filter((channel) => types.includes(channel.type))
    .map((channel) => ({
      value: channel.id,
      label: channel.name,
      glyph: channel.type === "4" ? "category" : channel.type === "5" ? "announce" : "text",
    }));
}

function colorToHex(color: number | null | undefined): string {
  if (typeof color !== "number" || !Number.isFinite(color)) return "";
  return `#${(color >>> 0).toString(16).padStart(6, "0").slice(-6).toUpperCase()}`;
}

function hexToColor(hex: string): number | null {
  if (!/^#[0-9A-Fa-f]{6}$/.test(hex.trim())) return null;
  return Number.parseInt(hex.trim().slice(1), 16);
}

interface DeliveryDraft {
  panel_channel: string | null;
  logging_channel: string | null;
  closed_category: string | null;
  panel_type: "button" | "dropdown";
}

export function TicketsWorkspace({
  guildId,
  initialConfig,
  channels,
  roles,
  botName,
  botAvatar,
}: {
  guildId: string;
  initialConfig: TicketConfig;
  channels: DiscordChannel[];
  roles: DiscordRole[];
  botName: string;
  botAvatar: string | null;
}) {
  const [config, setConfig] = useState(initialConfig);
  const delivery = useDraft<DeliveryDraft>({
    panel_channel: initialConfig.panel_channel,
    logging_channel: initialConfig.logging_channel ?? null,
    closed_category: initialConfig.closed_category ?? null,
    panel_type: initialConfig.panel_type === "dropdown" ? "dropdown" : "button",
  });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<{ index: number; data: TicketCategory } | null>(null);
  const [adding, setAdding] = useState(false);
  const [removeIndex, setRemoveIndex] = useState<number | null>(null);
  const [colorText, setColorText] = useState(colorToHex(initialConfig.embed?.color));

  const refresh = async (keepAppearance = false) => {
    const data = await api.getTickets(guildId);
    setConfig((current) => (keepAppearance ? { ...data, embed: current.embed } : data));
    if (!keepAppearance) setColorText(colorToHex(data.embed?.color));
  };

  const saveDelivery = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.updateTickets(guildId, delivery.draft);
      delivery.commit(delivery.draft);
      await refresh(true);
      toast.success("Ticket settings saved");
    } catch {
      setError("Could not save ticket settings.");
      toast.error("Could not save ticket settings");
    } finally {
      setSaving(false);
    }
  };

  const saveCategory = async () => {
    if (!editing || !editing.data.name.trim()) return;
    const next = [...config.categories];
    if (adding) next.push(editing.data);
    else next[editing.index] = editing.data;
    setSaving(true);
    try {
      await api.updateTickets(guildId, { categories: next });
      await refresh(true);
      setEditing(null);
      setAdding(false);
      toast.success("Category saved");
    } catch {
      toast.error("Could not save the category");
    } finally {
      setSaving(false);
    }
  };

  const removeCategory = async () => {
    if (removeIndex == null) return;
    const next = config.categories.filter((_, index) => index !== removeIndex);
    setSaving(true);
    try {
      await api.updateTickets(guildId, { categories: next });
      await refresh(true);
      setRemoveIndex(null);
      toast.success("Category removed");
    } catch {
      toast.error("Could not remove the category");
    } finally {
      setSaving(false);
    }
  };

  const saveAppearance = async () => {
    const color = colorText.trim() ? hexToColor(colorText) : null;
    if (colorText.trim() && color == null) {
      setError("Use a # colour, for example #6025E2.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      await api.updateTickets(guildId, {
        embed_title: config.embed?.title ?? null,
        embed_description: config.embed?.description ?? null,
        embed_color: color,
        embed_image_url: config.embed?.image_url ?? null,
        embed_thumbnail_url: config.embed?.thumbnail_url ?? null,
      });
      await refresh();
      toast.success("Panel appearance saved");
    } catch {
      setError("Could not save the panel appearance.");
      toast.error("Could not save the panel appearance");
    } finally {
      setSaving(false);
    }
  };

  const roleName = (id: string) => roles.find((role) => role.id === id)?.name ?? id;
  const textChannels = channelOptions(channels, ["0", "5"]);
  const categories = channelOptions(channels, ["4"]);
  const assignable = roles.filter((role) => role.name !== "@everyone" && !role.managed);
  const parsedColor = hexToColor(colorText);
  const previewColor = parsedColor == null ? "#2F3136" : colorToHex(parsedColor);

  return (
    <div>
      <PageHeader title="Tickets" description="Panels are published from Discord with the ticket command.">
        <span className="font-mono text-caption text-fg-3">
          {config.open_ticket_count} open · {config.categories.length} categories
        </span>
      </PageHeader>

      <SettingGroup id="ticket-delivery" label="Delivery">
        <SettingRow label="Panel channel" description="Where the ticket panel is posted." htmlFor="ticket-panel">
          <Combobox
            id="ticket-panel"
            value={delivery.draft.panel_channel}
            onValueChange={(value) => delivery.setDraft({ ...delivery.draft, panel_channel: value })}
            options={textChannels}
            placeholder="Select a channel"
            searchLabel="Search channels"
          />
        </SettingRow>
        <SettingRow label="Logging channel" description="Where ticket logs are sent." htmlFor="ticket-log">
          <Combobox
            id="ticket-log"
            value={delivery.draft.logging_channel}
            onValueChange={(value) => delivery.setDraft({ ...delivery.draft, logging_channel: value })}
            options={textChannels}
            placeholder="Select a channel"
            searchLabel="Search channels"
          />
        </SettingRow>
        <SettingRow label="Closed category" description="Category closed tickets move into." htmlFor="ticket-closed">
          <Combobox
            id="ticket-closed"
            value={delivery.draft.closed_category}
            onValueChange={(value) => delivery.setDraft({ ...delivery.draft, closed_category: value })}
            options={categories}
            placeholder="Select a category"
            searchLabel="Search categories"
          />
        </SettingRow>
        <SettingRow label="Panel type" description="How members pick a category.">
          <Segmented
            label="Panel type"
            value={delivery.draft.panel_type}
            onChange={(value) => delivery.setDraft({ ...delivery.draft, panel_type: value })}
            options={[
              { value: "button", label: "Buttons" },
              { value: "dropdown", label: "Dropdown" },
            ]}
          />
        </SettingRow>
      </SettingGroup>

      <SettingGroup id="ticket-categories" label="Categories" meta={String(config.categories.length)}>
        <div className="mt-2 border-t border-line">
          {config.categories.length === 0 ? (
            <p className="py-3 text-small text-fg-3" dir="auto">No categories yet.</p>
          ) : (
            config.categories.map((category, index) => (
              <div key={`${category.name}-${index}`} className="grid items-center gap-2 border-b border-line-subtle py-2 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]">
                <span className="text-body text-fg-1">
                  {category.emoji ? `${category.emoji} ` : ""}
                  {category.name}
                </span>
                <span className="truncate text-small text-fg-3">
                  {category.staff_roles.length
                    ? category.staff_roles.map((id) => roleName(id)).join(", ")
                    : "No staff roles"}
                </span>
                <span className="flex gap-1">
                  <Button
                    type="button"
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setAdding(false);
                      setEditing({ index, data: { ...category, staff_roles: [...category.staff_roles] } });
                    }}
                  >
                    Edit
                  </Button>
                  <Button type="button" variant="danger-secondary" size="sm" onClick={() => setRemoveIndex(index)}>
                    Delete
                  </Button>
                </span>
              </div>
            ))
          )}
        </div>
        <div className="mt-3">
          <Button
            type="button"
            variant="secondary"
            onClick={() => {
              setAdding(true);
              setEditing({
                index: -1,
                data: { name: "", emoji: "", staff_roles: [], button_style: 2, discord_category_id: null },
              });
            }}
          >
            Add category
          </Button>
        </div>
      </SettingGroup>

      <SettingGroup id="ticket-appearance" label="Panel appearance">
        <div className="mt-3 grid items-start gap-6 lg:grid-cols-[minmax(280px,420px)_minmax(0,1fr)]">
          <div className="space-y-3">
            <label className="block text-small text-fg-2">
              Title
              <Input
                value={config.embed?.title ?? ""}
                onChange={(event) => setConfig({ ...config, embed: { ...config.embed, title: event.target.value } })}
                className="mt-1"
              />
            </label>
            <label className="block text-small text-fg-2">
              Description
              <textarea
                value={config.embed?.description ?? ""}
                onChange={(event) => setConfig({ ...config, embed: { ...config.embed, description: event.target.value } })}
                className="mt-1 min-h-24 w-full rounded-sm border border-line-input bg-surface-well p-2 text-body text-fg-1 outline-none focus-visible:border-brand-400"
              />
            </label>
            <label className="block text-small text-fg-2">
              Colour
              <Input value={colorText} onChange={(event) => setColorText(event.target.value)} placeholder="#2F3136" className="mt-1" />
            </label>
            <Button type="button" variant="secondary" onClick={() => void saveAppearance()} disabled={saving}>
              Save appearance
            </Button>
          </div>
          <div className="border border-line-subtle">
            <DiscordPreview
              mode="channel"
              channelName={channels.find((channel) => channel.id === delivery.draft.panel_channel)?.name}
              botName={botName}
              botAvatar={botAvatar}
              content=""
              warnTokens={[]}
              width="desktop"
              note="Preview of the panel embed. Buttons come from the categories above."
              embed={{
                title: config.embed?.title ?? "",
                description: config.embed?.description ?? "",
                color: previewColor,
                authorName: "",
                authorIcon: null,
                footerText: "",
                footerIcon: null,
                thumbnail: config.embed?.thumbnail_url || null,
                image: config.embed?.image_url || null,
              }}
            />
          </div>
        </div>
      </SettingGroup>

      <SaveBar
        dirty={delivery.dirty}
        saving={saving}
        error={error}
        onSave={() => void saveDelivery()}
        onDiscard={() => {
          delivery.reset();
          setError(null);
        }}
      />

      <Dialog open={editing != null} onOpenChange={(open) => !open && setEditing(null)}>
        <DialogContent wide>
          <DialogHeader>
            <DialogTitle>{adding ? "Add category" : "Edit category"}</DialogTitle>
            <DialogDescription>Name, staff roles, and where new tickets are created.</DialogDescription>
          </DialogHeader>
          {editing ? (
            <div className="space-y-3 px-4 py-3">
              <label className="block text-small text-fg-2">
                Name
                <Input
                  value={editing.data.name}
                  onChange={(event) => setEditing({ ...editing, data: { ...editing.data, name: event.target.value } })}
                  className="mt-1"
                />
              </label>
              <label className="block text-small text-fg-2">
                Emoji
                <Input
                  value={editing.data.emoji ?? ""}
                  onChange={(event) => setEditing({ ...editing, data: { ...editing.data, emoji: event.target.value } })}
                  className="mt-1"
                />
              </label>
              <label className="block text-small text-fg-2">
                Button style
                <span className="mt-1 block">
                  <Segmented
                    label="Button style"
                    value={String(editing.data.button_style ?? 2)}
                    onChange={(value) =>
                      setEditing({ ...editing, data: { ...editing.data, button_style: Number(value) } })
                    }
                    options={[
                      { value: "2", label: "Blurple" },
                      { value: "1", label: "Grey" },
                      { value: "3", label: "Green" },
                      { value: "4", label: "Red" },
                    ]}
                  />
                </span>
              </label>
              <label className="block text-small text-fg-2">
                Ticket category
                <span className="mt-1 block">
                  <Combobox
                    value={editing.data.discord_category_id ?? null}
                    onValueChange={(value) => setEditing({ ...editing, data: { ...editing.data, discord_category_id: value } })}
                    options={categories}
                    placeholder="Select a category"
                    searchLabel="Search categories"
                  />
                </span>
              </label>
              <div>
                <p className="text-small text-fg-2">Staff roles</p>
                <ul className="mt-1 space-y-1">
                  {editing.data.staff_roles.map((id) => (
                    <li key={id} className="flex items-center justify-between gap-2 text-body text-fg-1">
                      <span className="inline-flex items-center gap-2">
                        <span className="size-2.5 rounded-full" style={{ background: roleSwatch(roles.find((role) => role.id === id)?.color) ?? "transparent" }} />
                        {roleName(id)}
                      </span>
                      <Button
                        type="button"
                        variant="ghost"
                        size="sm"
                        onClick={() =>
                          setEditing({
                            ...editing,
                            data: { ...editing.data, staff_roles: editing.data.staff_roles.filter((roleId) => roleId !== id) },
                          })
                        }
                      >
                        Remove
                      </Button>
                    </li>
                  ))}
                </ul>
                <div className="mt-2">
                  <Combobox
                    value={null}
                    onValueChange={(value) => {
                      if (!value || editing.data.staff_roles.includes(value)) return;
                      setEditing({ ...editing, data: { ...editing.data, staff_roles: [...editing.data.staff_roles, value] } });
                    }}
                    options={assignable.map((role) => ({ value: role.id, label: role.name, swatch: roleSwatch(role.color) }))}
                    placeholder="Add a staff role"
                    searchLabel="Search roles"
                  />
                </div>
              </div>
            </div>
          ) : null}
          <DialogFooter>
            <Button type="button" variant="secondary" onClick={() => setEditing(null)}>
              Cancel
            </Button>
            <Button type="button" onClick={() => void saveCategory()} disabled={saving || !editing?.data.name.trim()}>
              Save category
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      <Dialog open={removeIndex != null} onOpenChange={(open) => !open && setRemoveIndex(null)}>
        <DialogContent wide>
          <DialogHeader>
            <DialogTitle>Delete this category?</DialogTitle>
            <DialogDescription>The category is removed from the panel configuration. Open tickets are not closed.</DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button type="button" variant="secondary" onClick={() => setRemoveIndex(null)}>
              Cancel
            </Button>
            <Button type="button" variant="danger" onClick={() => void removeCategory()} disabled={saving}>
              Delete category
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
