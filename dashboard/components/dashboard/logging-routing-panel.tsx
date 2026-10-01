"use client";

import React, { useState } from "react";
import { Button } from "@/components/ui/button";
import { Dialog, DialogBody, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { StatusLabel, type Status } from "@/components/ui/status";
import { Switch } from "@/components/ui/switch";

type RouteRow = {
  category: string;
  enabled: boolean;
  channel_id: string | null;
  channel_name?: string | null;
  delivery?: string;
};

type Group = { category: string; label: string; events: Array<{ id: string; label: string }> };
type EventRoute = { event_type: string; mode: string; channel_id: string | null };
type IgnoreUser = { id: string; display_name?: string | null; username?: string | null };

const HEALTH: Record<string, { status: Status; label: string }> = {
  delivering: { status: "healthy", label: "Healthy" },
  stored_only: { status: "disabled", label: "Stored only" },
  missing_channel: { status: "warning", label: "Channel missing" },
  bot_cannot_view: { status: "critical", label: "Cannot view" },
  bot_cannot_send: { status: "critical", label: "Cannot send" },
  bot_cannot_embed: { status: "critical", label: "Cannot embed" },
  channel_unavailable: { status: "critical", label: "Unavailable" },
  unchecked: { status: "unknown", label: "Not checked" },
};

export function LoggingRoutingPanel({
  routes,
  groups,
  eventRoutes,
  channels,
  roles,
  ignoredChannels,
  ignoredRoles,
  ignoredUsers,
  onRoute,
  onEventRoute,
  onTest,
  onEventTest,
  onIgnores,
  onSearchMembers,
}: {
  routes: RouteRow[];
  groups: Group[];
  eventRoutes: EventRoute[];
  channels: Array<{ id: string; name: string; type?: string | number }>;
  roles: Array<{ id: string; name: string }>;
  ignoredChannels: string[];
  ignoredRoles: string[];
  ignoredUsers: IgnoreUser[];
  onRoute: (row: RouteRow) => void;
  onEventRoute: (eventType: string, mode: string, channelId: string | null) => void;
  onTest: (category: string) => void;
  onEventTest: (eventType: string) => void;
  onIgnores: (next: { channels: string[]; roles: string[]; users: IgnoreUser[] }) => void;
  onSearchMembers: (query: string) => Promise<IgnoreUser[]>;
}) {
  const [mode, setMode] = useState<"simple" | "advanced">("simple");
  const [open, setOpen] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [exclusions, setExclusions] = useState(false);
  const textChannels = channels.filter((channel) => ["0", "5", "text", "news"].includes(String(channel.type ?? "0")));
  const channelOptions = textChannels.map((channel) => ({ value: channel.id, label: `#${channel.name}` }));
  const routeFor = (category: string) => routes.find((row) => row.category === category);
  const override = (eventType: string) => eventRoutes.find((row) => row.event_type === eventType);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-3">
        <div className="flex gap-1">
          {(["simple", "advanced"] as const).map((item) => (
            <button
              key={item}
              type="button"
              className={`px-2 py-1 text-small capitalize ${mode === item ? "bg-bg-2 text-fg-1 ring-1 ring-brand-400" : "text-fg-2 ring-1 ring-line"}`}
              onClick={() => setMode(item)}
            >
              {item}
            </button>
          ))}
        </div>
        <button type="button" className="text-small text-fg-2" onClick={() => setExclusions(true)}>
          Message exclusions · Channels {ignoredChannels.length} · Roles {ignoredRoles.length} · Members {ignoredUsers.length}
        </button>
      </div>

      {mode === "simple" ? (
        <ul className="divide-y divide-line-subtle border-y border-line-subtle">
          {groups.map((group) => {
            const route = routeFor(group.category);
            const enabledCount = group.events.filter((event) => (override(event.id)?.mode || "inherit") !== "disabled").length;
            const health = HEALTH[route?.delivery || (route?.enabled ? "unchecked" : "stored_only")] ?? HEALTH.unchecked;
            const destination = route?.channel_name ? `#${route.channel_name}` : route?.enabled ? "Channel missing" : "Stored only";
            return (
              <li key={group.category} className="py-2">
                <div className="flex items-center justify-between gap-3">
                  <div className="min-w-0">
                    <p className="text-small text-fg-1">{group.label}</p>
                    <p className="text-caption text-fg-3">
                      {enabledCount} event{enabledCount === 1 ? "" : "s"} enabled · {destination}
                    </p>
                  </div>
                  <div className="flex items-center gap-2">
                    <StatusLabel status={health.status}>{health.label}</StatusLabel>
                    <Button type="button" variant="secondary" onClick={() => setOpen(open === group.category ? null : group.category)}>
                      {open === group.category ? "Close" : "Configure"}
                    </Button>
                  </div>
                </div>
                {open === group.category && route ? (
                  <div className="mt-2 flex flex-wrap items-center gap-2">
                    <Switch checked={route.enabled} aria-label={`${group.label} enabled`} onCheckedChange={(enabled) => onRoute({ ...route, enabled })} />
                    <div className="w-52">
                      <Select
                        value={route.channel_id ?? ""}
                        options={[{ value: "", label: "No channel" }, ...channelOptions]}
                        placeholder="Destination"
                        onValueChange={(channelId) => onRoute({ ...route, channel_id: channelId || null, enabled: Boolean(channelId) || route.enabled })}
                      />
                    </div>
                    <Button type="button" variant="secondary" disabled={!route.enabled || !route.channel_id} onClick={() => onTest(group.category)}>
                      Send test log
                    </Button>
                  </div>
                ) : null}
              </li>
            );
          })}
        </ul>
      ) : (
        <ul className="divide-y divide-line-subtle border-y border-line-subtle">
          {groups.map((group) => {
            const route = routeFor(group.category);
            const custom = group.events.filter((event) => override(event.id)?.mode === "custom").length;
            const enabledCount = group.events.filter((event) => (override(event.id)?.mode || "inherit") !== "disabled").length;
            return (
              <li key={group.category} className="py-2">
                <button type="button" className="flex w-full items-center justify-between gap-3 text-start" onClick={() => setExpanded(expanded === group.category ? null : group.category)}>
                  <span>
                    <span className="block text-small text-fg-1">{group.label}</span>
                    <span className="block text-caption text-fg-3">
                      Default {route?.channel_name ? `#${route.channel_name}` : "stored only"} · {enabledCount} enabled
                      {custom ? ` · ${custom} custom route${custom === 1 ? "" : "s"}` : ""}
                    </span>
                  </span>
                  <span className="text-caption text-fg-3">{expanded === group.category ? "Hide" : "Expand"}</span>
                </button>
                {expanded === group.category ? (
                  <ul className="mt-2 space-y-2">
                    {group.events.map((event) => {
                      const row = override(event.id);
                      const current = row?.mode === "custom" && row.channel_id ? `channel:${row.channel_id}` : row?.mode || "inherit";
                      return (
                        <li key={event.id} className="grid items-center gap-2 sm:grid-cols-[minmax(0,1fr)_16rem_auto]">
                          <span className="text-small text-fg-1">{event.label}</span>
                          <Select
                            value={current}
                            options={[
                              { value: "inherit", label: "Inherit category" },
                              { value: "stored_only", label: "Stored only" },
                              { value: "disabled", label: "Disabled" },
                              ...channelOptions.map((channel) => ({ value: `channel:${channel.value}`, label: channel.label })),
                            ]}
                            onValueChange={(value) => {
                              if (value.startsWith("channel:")) onEventRoute(event.id, "custom", value.slice(8));
                              else onEventRoute(event.id, value, null);
                            }}
                          />
                          {row?.mode === "custom" ? (
                            <Button type="button" variant="secondary" onClick={() => onEventTest(event.id)}>
                              Test
                            </Button>
                          ) : (
                            <span />
                          )}
                        </li>
                      );
                    })}
                  </ul>
                ) : null}
              </li>
            );
          })}
        </ul>
      )}

      <Dialog open={exclusions} onOpenChange={setExclusions}>
        <DialogContent wide>
          <DialogHeader>
            <DialogTitle>Message exclusions</DialogTitle>
          </DialogHeader>
          <DialogBody>
            <Exclusions
              channels={textChannels}
              roles={roles}
              ignoredChannels={ignoredChannels}
              ignoredRoles={ignoredRoles}
              ignoredUsers={ignoredUsers}
              onIgnores={onIgnores}
              onSearchMembers={onSearchMembers}
            />
          </DialogBody>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function Exclusions({
  channels,
  roles,
  ignoredChannels,
  ignoredRoles,
  ignoredUsers,
  onIgnores,
  onSearchMembers,
}: {
  channels: Array<{ id: string; name: string }>;
  roles: Array<{ id: string; name: string }>;
  ignoredChannels: string[];
  ignoredRoles: string[];
  ignoredUsers: IgnoreUser[];
  onIgnores: (next: { channels: string[]; roles: string[]; users: IgnoreUser[] }) => void;
  onSearchMembers: (query: string) => Promise<IgnoreUser[]>;
}) {
  const [tab, setTab] = useState<"channels" | "roles" | "members">("channels");
  const [query, setQuery] = useState("");
  const [hits, setHits] = useState<IgnoreUser[]>([]);
  const needle = query.trim().toLowerCase();
  return (
    <div>
      <div className="mb-3 flex gap-1">
        {(["channels", "roles", "members"] as const).map((item) => (
          <button key={item} type="button" className={`px-2 py-1 text-small capitalize ${tab === item ? "bg-bg-2 text-fg-1" : "text-fg-3"}`} onClick={() => setTab(item)}>
            {item}
          </button>
        ))}
      </div>
      <Input
        value={query}
        placeholder={tab === "members" ? "Search members" : "Filter"}
        aria-label="Filter exclusions"
        onChange={(event) => {
          const value = event.target.value;
          setQuery(value);
          if (tab === "members" && value.trim().length >= 2) void onSearchMembers(value.trim()).then(setHits);
          else setHits([]);
        }}
      />
      {tab === "channels" ? (
        <CheckList
          options={channels.filter((channel) => channel.name.toLowerCase().includes(needle)).map((channel) => ({ id: channel.id, label: `#${channel.name}` }))}
          selected={ignoredChannels}
          onChange={(channels) => onIgnores({ channels, roles: ignoredRoles, users: ignoredUsers })}
        />
      ) : null}
      {tab === "roles" ? (
        <CheckList
          options={roles.filter((role) => role.name !== "@everyone" && role.name.toLowerCase().includes(needle)).map((role) => ({ id: role.id, label: `@${role.name}` }))}
          selected={ignoredRoles}
          onChange={(roles) => onIgnores({ channels: ignoredChannels, roles, users: ignoredUsers })}
        />
      ) : null}
      {tab === "members" ? (
        <div className="mt-2">
          <ul className="space-y-1">
            {hits.map((member) => (
              <li key={member.id}>
                <button
                  type="button"
                  className="text-small text-fg-1"
                  onClick={() => {
                    if (!ignoredUsers.some((user) => user.id === member.id)) onIgnores({ channels: ignoredChannels, roles: ignoredRoles, users: [...ignoredUsers, member] });
                    setHits([]);
                    setQuery("");
                  }}
                >
                  Add {member.display_name || member.username || "member"}
                </button>
              </li>
            ))}
          </ul>
          <ul className="mt-2 space-y-1">
            {ignoredUsers.map((user) => (
              <li key={user.id} className="flex items-center justify-between text-small">
                <span>{user.display_name || user.username || "Unknown member"}</span>
                <button type="button" className="text-caption text-fg-3" onClick={() => onIgnores({ channels: ignoredChannels, roles: ignoredRoles, users: ignoredUsers.filter((item) => item.id !== user.id) })}>
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function CheckList({ options, selected, onChange }: { options: Array<{ id: string; label: string }>; selected: string[]; onChange: (ids: string[]) => void }) {
  return (
    <ul className="mt-2 max-h-64 space-y-1 overflow-y-auto">
      {options.map((option) => {
        const checked = selected.includes(option.id);
        return (
          <li key={option.id}>
            <label className="flex items-center gap-2 text-small">
              <input type="checkbox" checked={checked} onChange={() => onChange(checked ? selected.filter((id) => id !== option.id) : [...selected, option.id])} />
              {option.label}
            </label>
          </li>
        );
      })}
    </ul>
  );
}
