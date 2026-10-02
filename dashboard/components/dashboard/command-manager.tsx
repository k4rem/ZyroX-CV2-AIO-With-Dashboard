"use client";

import React, { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { ChannelPicker, RolePicker, type ChannelOption } from "@/components/discord/channel-picker";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { StatusLabel } from "@/components/ui/status";
import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api";
import { commandCategories, filterCommands, restrictionSummary, type CommandRow } from "@/lib/commands";

function normalize(row: CommandRow): CommandRow {
  return {
    ...row,
    category: row.category || row.module || "General",
    description: row.description || "",
    usage: row.usage || row.name,
    aliases: row.aliases || [],
    cooldown: row.cooldown || null,
    permissions: row.permissions || [],
    protected: Boolean(row.protected),
    allowed_role_ids: row.allowed_role_ids || [],
    blocked_role_ids: row.blocked_role_ids || [],
    allowed_channel_ids: row.allowed_channel_ids || [],
    blocked_channel_ids: row.blocked_channel_ids || [],
  };
}

function addId(ids: string[], id: string) {
  return id && !ids.includes(id) ? [...ids, id] : ids;
}

function ScopeList({
  label,
  ids,
  nameFor,
  onRemove,
  picker,
}: {
  label: string;
  ids: string[];
  nameFor: (id: string) => string;
  onRemove: (id: string) => void;
  picker: React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      <p className="text-caption text-fg-3">{label}</p>
      {picker}
      {ids.length ? (
        <ul className="flex flex-wrap gap-1">
          {ids.map((id) => (
            <li key={id}>
              <button type="button" className="rounded-sm border border-line bg-surface-2 px-2 py-1 text-caption text-fg-1 hover:border-line-strong" onClick={() => onRemove(id)}>
                {nameFor(id)} · remove
              </button>
            </li>
          ))}
        </ul>
      ) : (
        <p className="text-caption text-fg-4">None</p>
      )}
    </div>
  );
}

export function CommandManager({ guildId, initial }: { guildId: string; initial: CommandRow[] }) {
  const [rows, setRows] = useState(initial.map(normalize));
  const [query, setQuery] = useState("");
  const [category, setCategory] = useState("all");
  const [enabled, setEnabled] = useState<"all" | "on" | "off">("all");
  const [selected, setSelected] = useState<string | null>(null);
  const [draft, setDraft] = useState<CommandRow | null>(null);
  const [roles, setRoles] = useState<{ id: string; name: string }[]>([]);
  const [channels, setChannels] = useState<ChannelOption[]>([]);
  const [saving, setSaving] = useState(false);
  const [page, setPage] = useState(0);
  const pageSize = 40;

  useEffect(() => {
    api.getRoles(guildId).then((body) => setRoles(Array.isArray(body) ? body : [])).catch(() => setRoles([]));
    api.getChannels(guildId).then((body) => setChannels(Array.isArray(body) ? body : [])).catch(() => setChannels([]));
  }, [guildId]);

  const categories = useMemo(() => commandCategories(rows), [rows]);
  const visible = useMemo(() => filterCommands(rows, query, category, enabled), [rows, query, category, enabled]);
  const pageCount = Math.max(1, Math.ceil(visible.length / pageSize));
  useEffect(() => {
    setPage(0);
  }, [query, category, enabled]);
  const roleName = (id: string) => roles.find((role) => role.id === id)?.name || "Unknown role";
  const channelName = (id: string) => {
    const channel = channels.find((item) => item.id === id);
    return channel ? `#${channel.name}` : "Unknown channel";
  };

  function open(row: CommandRow) {
    setSelected(row.name);
    setDraft({ ...row });
  }

  function patch(partial: Partial<CommandRow>) {
    setDraft((current) => (current ? { ...current, ...partial } : current));
  }

  async function save() {
    if (!draft || draft.protected) return;
    setSaving(true);
    try {
      await api.updateCommand(guildId, {
        command_name: draft.name,
        enabled: draft.enabled,
        allowed_role_ids: draft.allowed_role_ids,
        blocked_role_ids: draft.blocked_role_ids,
        allowed_channel_ids: draft.allowed_channel_ids,
        blocked_channel_ids: draft.blocked_channel_ids,
      });
      setRows((current) => current.map((row) => (row.name === draft.name ? draft : row)));
      toast.success("Command updated");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not update the command");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader title="Commands" description="Turn commands on or off, and limit who can use them and where." />
      <div className="grid grid-cols-1 gap-2 sm:grid-cols-3">
        <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search commands" />
        <Select
          value={category}
          onValueChange={setCategory}
          options={[{ value: "all", label: "All categories" }, ...categories.map((name) => ({ value: name, label: name }))]}
        />
        <Select
          value={enabled}
          onValueChange={(value) => setEnabled(value as "all" | "on" | "off")}
          options={[{ value: "all", label: "On and off" }, { value: "on", label: "Enabled" }, { value: "off", label: "Disabled" }]}
        />
      </div>
      <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="min-w-0 border border-line-subtle">
          {category === "all" && !query.trim() ? (
            <ul className="grid grid-cols-1 sm:grid-cols-2">
              {categories.map((name) => (
                <li key={name} className="border-b border-line-subtle">
                  <button type="button" className="flex w-full items-center justify-between px-3 py-2 text-start hover:bg-surface-1" onClick={() => setCategory(name)}>
                    <span className="text-small text-fg-1">{name}</span>
                    <span className="text-caption text-fg-3">{rows.filter((row) => row.category === name).length}</span>
                  </button>
                </li>
              ))}
            </ul>
          ) : visible.length === 0 ? (
            <p className="px-3 py-4 text-small text-fg-3">No commands match.</p>
          ) : (
            <ul className="divide-y divide-line-subtle">
              {visible.slice(page * pageSize, page * pageSize + pageSize).map((row) => (
                <li key={row.name}>
                  <button
                    type="button"
                    className="grid w-full grid-cols-1 gap-1 px-3 py-2 text-start hover:bg-surface-1 md:grid-cols-[minmax(0,1fr)_8rem_9rem] md:items-center"
                    onClick={() => open(row)}
                  >
                    <span className="min-w-0">
                      <span className="block font-mono text-small text-fg-1">{row.name}</span>
                      <span className="block truncate text-caption text-fg-3">{row.description || row.category}</span>
                    </span>
                    <span className="text-caption text-fg-3">{row.category}</span>
                    <span className="flex items-center justify-between gap-2 md:justify-end">
                      <span className="text-caption text-fg-2">{restrictionSummary(row)}</span>
                      {row.protected ? <StatusLabel status="warning">Protected</StatusLabel> : row.enabled ? <StatusLabel status="healthy">On</StatusLabel> : <StatusLabel status="disabled">Off</StatusLabel>}
                    </span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {category !== "all" || query.trim() ? visible.length > pageSize ? (
            <div className="flex items-center justify-between border-t border-line-subtle px-3 py-2">
              <span className="text-caption text-fg-3">{page * pageSize + 1}–{Math.min(visible.length, page * pageSize + pageSize)} of {visible.length}</span>
              <div className="flex gap-2">
                <Button type="button" variant="ghost" disabled={page === 0} onClick={() => setPage((current) => current - 1)}>Previous</Button>
                <Button type="button" variant="ghost" disabled={page + 1 >= pageCount} onClick={() => setPage((current) => current + 1)}>Next</Button>
              </div>
            </div>
          ) : null : null}
        </div>
        {draft && selected ? (
          <aside className="space-y-3 border border-line bg-surface-1 p-3">
            <div>
              <p className="font-mono text-body text-fg-1">{draft.name}</p>
              <p className="mt-1 text-small text-fg-2">{draft.description || "No description."}</p>
            </div>
            <p className="text-caption text-fg-3">Usage <span className="font-mono text-fg-2">{draft.usage || draft.name}</span></p>
            {draft.aliases.length ? <p className="text-caption text-fg-3">Aliases {draft.aliases.join(", ")}</p> : null}
            {draft.permissions.length ? <p className="text-caption text-fg-3">Permissions {draft.permissions.join(", ")}</p> : null}
            {draft.cooldown ? <p className="text-caption text-fg-3">Cooldown {draft.cooldown.rate} / {draft.cooldown.per}s</p> : null}
            {draft.protected ? (
              <p className="text-small text-fg-2">Required for recovery. This command stays available.</p>
            ) : (
              <>
                <label className="flex items-center justify-between gap-3 text-small text-fg-1">
                  Enabled
                  <Switch checked={draft.enabled} aria-label={`${draft.name} enabled`} onCheckedChange={(value) => patch({ enabled: value })} />
                </label>
                <ScopeList
                  label="Allowed roles"
                  ids={draft.allowed_role_ids}
                  nameFor={roleName}
                  onRemove={(id) => patch({ allowed_role_ids: draft.allowed_role_ids.filter((item) => item !== id) })}
                  picker={<RolePicker roles={roles} value="" onChange={(id) => patch({ allowed_role_ids: addId(draft.allowed_role_ids, id) })} />}
                />
                <ScopeList
                  label="Blocked roles"
                  ids={draft.blocked_role_ids}
                  nameFor={roleName}
                  onRemove={(id) => patch({ blocked_role_ids: draft.blocked_role_ids.filter((item) => item !== id) })}
                  picker={<RolePicker roles={roles} value="" onChange={(id) => patch({ blocked_role_ids: addId(draft.blocked_role_ids, id) })} />}
                />
                <ScopeList
                  label="Allowed channels"
                  ids={draft.allowed_channel_ids}
                  nameFor={channelName}
                  onRemove={(id) => patch({ allowed_channel_ids: draft.allowed_channel_ids.filter((item) => item !== id) })}
                  picker={<ChannelPicker channels={channels} value="" onChange={(id) => patch({ allowed_channel_ids: addId(draft.allowed_channel_ids, id) })} />}
                />
                <ScopeList
                  label="Blocked channels"
                  ids={draft.blocked_channel_ids}
                  nameFor={channelName}
                  onRemove={(id) => patch({ blocked_channel_ids: draft.blocked_channel_ids.filter((item) => item !== id) })}
                  picker={<ChannelPicker channels={channels} value="" onChange={(id) => patch({ blocked_channel_ids: addId(draft.blocked_channel_ids, id) })} />}
                />
                <Button type="button" onClick={() => void save()} loading={saving}>Save</Button>
              </>
            )}
          </aside>
        ) : (
          <p className="text-small text-fg-3">Select a command to change who can use it.</p>
        )}
      </div>
    </div>
  );
}

