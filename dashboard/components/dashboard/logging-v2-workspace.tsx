"use client";

import React, { useMemo, useState } from "react";
import {
  Hash,
  MessageSquare,
  Mic,
  Settings,
  Shield,
  UserRound,
} from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { StatusLabel, type Status } from "@/components/ui/status";
import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api";

const LABELS: Record<string, string> = {
  message_events: "Messages",
  join_leave_events: "Joins and leaves",
  member_moderation: "Members",
  voice_events: "Voice",
  role_events: "Roles",
  channel_events: "Channels",
  guild_events: "Server",
  bot_actions: "Bot actions",
};

const DELIVERY: Record<string, { status: Status; label: string }> = {
  delivering: { status: "healthy", label: "Delivering" },
  stored_only: { status: "warning", label: "Stored only" },
  missing_permission: { status: "critical", label: "Missing permission" },
  channel_unavailable: { status: "critical", label: "Channel unavailable" },
  disabled: { status: "disabled", label: "Disabled" },
  unchecked: { status: "unknown", label: "Not checked" },
};

type Entity = {
  id?: string;
  display_name?: string | null;
  username?: string | null;
  name?: string | null;
  avatar_url?: string | null;
  color?: string | null;
};

type Field = { name: string; dashboard: string; discord?: string };

type Presentation = {
  title: string;
  summary: string;
  change_line?: string;
  category_label: string;
  actor?: Entity | null;
  target?: Entity | null;
  channel?: Entity | null;
  fields?: Field[];
  changes?: Array<{ label: string; value: string }>;
  jump_url?: string | null;
  incident_id?: string | null;
};

type EventRow = {
  id: string;
  category: string;
  event_type: string;
  occurred_at: string;
  presentation?: Presentation;
};

type RouteRow = {
  category: string;
  enabled: boolean;
  channel_id: string | null;
  channel_name?: string | null;
  delivery?: string;
};

type IgnoreUser = { id: string; display_name?: string | null; username?: string | null; avatar_url?: string | null };
type IgnoreRef = { id: string; name?: string | null };

type Home = {
  overview: {
    total: number;
    by_category: Record<string, number>;
    series: Array<{ day: string; count: number }>;
  };
  routes: RouteRow[];
  events: EventRow[];
  next_cursor: string | null;
  event_types?: Array<{ id: string; label: string; category: string }>;
  retention?: { events_days: number; message_content_days: number };
  ignores?: { channels: IgnoreRef[]; roles: IgnoreRef[]; users: IgnoreUser[] };
};

function relativeTime(iso: string) {
  const delta = Date.now() - new Date(iso).getTime();
  const minutes = Math.round(delta / 60000);
  if (Number.isNaN(minutes)) return "";
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes} minute${minutes === 1 ? "" : "s"} ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours} hour${hours === 1 ? "" : "s"} ago`;
  const days = Math.round(hours / 24);
  return `${days} day${days === 1 ? "" : "s"} ago`;
}

function personName(entity?: Entity | null) {
  return entity?.display_name || entity?.username || entity?.name || null;
}

function EventIcon({ category }: { category: string }) {
  const className = "size-3.5 text-fg-3";
  if (category === "message_events") return <MessageSquare className={className} aria-hidden />;
  if (category === "voice_events") return <Mic className={className} aria-hidden />;
  if (category === "channel_events") return <Hash className={className} aria-hidden />;
  if (category === "guild_events" || category === "bot_actions") return <Settings className={className} aria-hidden />;
  if (category === "role_events") return <Shield className={className} aria-hidden />;
  return <UserRound className={className} aria-hidden />;
}

function Avatar({ entity }: { entity?: Entity | null }) {
  const name = personName(entity) || "?";
  if (entity?.avatar_url) {
    // Discord avatar hosts are not in the image allowlist.
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={entity.avatar_url} alt="" className="size-7 rounded-full object-cover" />;
  }
  return (
    <span className="grid size-7 place-items-center rounded-full bg-bg-2 text-caption text-fg-2">
      {name.slice(0, 1).toUpperCase()}
    </span>
  );
}

export function LoggingV2Workspace({
  guildId,
  initial,
  channels,
  roles,
}: {
  guildId: string;
  initial: Home;
  channels: Array<{ id: string; name: string; type?: string | number }>;
  roles: Array<{ id: string; name: string; color?: number }>;
}) {
  const [data, setData] = useState(initial);
  const [category, setCategory] = useState("");
  const [eventType, setEventType] = useState("");
  const [search, setSearch] = useState("");
  const [memberId, setMemberId] = useState("");
  const [suggestions, setSuggestions] = useState<IgnoreUser[]>([]);
  const [since, setSince] = useState("");
  const [until, setUntil] = useState("");
  const [detail, setDetail] = useState<EventRow | null>(null);
  const [routes, setRoutes] = useState(initial.routes);
  const [ignoredChannels, setIgnoredChannels] = useState((initial.ignores?.channels ?? []).map((item) => item.id));
  const [ignoredRoles, setIgnoredRoles] = useState((initial.ignores?.roles ?? []).map((item) => item.id));
  const [ignoredUsers, setIgnoredUsers] = useState<IgnoreUser[]>(initial.ignores?.users ?? []);
  const [userQuery, setUserQuery] = useState("");
  const [userHits, setUserHits] = useState<IgnoreUser[]>([]);

  const textChannels = channels.filter((channel) => {
    const type = String(channel.type ?? "0");
    return type === "0" || type === "5" || type === "text" || type === "news";
  });
  const channelOptions = textChannels.map((channel) => ({ value: channel.id, label: `#${channel.name}` }));
  const typeOptions = (data.event_types ?? []).filter((item) => !category || item.category === category);

  const load = async (cursor?: string | null) => {
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (eventType) params.set("event_type", eventType);
    if (memberId) params.set("member_id", memberId);
    else if (search.trim()) params.set("q", search.trim());
    if (since) params.set("since", new Date(since).toISOString());
    if (until) params.set("until", new Date(until).toISOString());
    if (cursor) params.set("cursor", cursor);
    const next = await api.getLoggingV2(guildId, params.size ? `?${params.toString()}` : "");
    setData(next);
    setRoutes(next.routes);
    setDetail(null);
  };

  const saveRoute = async (item: RouteRow) => {
    try {
      const saved = await api.updateLoggingRoute(guildId, {
        category: item.category,
        enabled: item.enabled,
        channel_id: item.channel_id,
      });
      setRoutes((current) => current.map((row) => (row.category === item.category ? { ...row, ...saved } : row)));
      toast.success("Route saved");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not save the route");
    }
  };

  const sendTest = async (item: RouteRow) => {
    try {
      await api.sendLoggingTest(guildId, item.category);
      toast.success(`Test log sent to #${item.channel_name || "the log channel"}`);
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not send the test log");
    }
  };

  const saveIgnores = async (next: { channels: string[]; roles: string[]; users: IgnoreUser[] }) => {
    try {
      const saved = await api.updateLoggingIgnores(guildId, {
        channels: next.channels,
        roles: next.roles,
        users: next.users.map((user) => user.id),
      });
      setIgnoredChannels((saved.channels ?? []).map((item: IgnoreRef) => item.id));
      setIgnoredRoles((saved.roles ?? []).map((item: IgnoreRef) => item.id));
      setIgnoredUsers(saved.users ?? []);
      toast.success("Ignore list saved");
    } catch (error) {
      toast.error(error instanceof Error ? error.message : "Could not save ignores");
    }
  };

  const lookup = async (value: string, assign: (members: IgnoreUser[]) => void) => {
    if (value.trim().length < 2) {
      assign([]);
      return;
    }
    try {
      const result = await api.searchLoggingMembers(guildId, value.trim());
      assign(result.members ?? []);
    } catch {
      assign([]);
    }
  };

  const series = useMemo(() => data.overview.series.slice(-14), [data.overview.series]);
  const max = Math.max(1, ...series.map((point) => point.count));
  const retention = data.retention ?? initial.retention ?? { events_days: 90, message_content_days: 30 };
  const view = detail?.presentation;

  return (
    <div className="space-y-8">
      <PageHeader
        title="Logging"
        description="Human-readable server activity, routed to the channels you choose."
      />

      {data.overview.total === 0 ? (
        <p className="text-small text-fg-3">No stored events yet. Activity appears here after the bot records it.</p>
      ) : series.length > 0 ? (
        <div>
          <p className="mb-2 text-caption text-fg-3">Events over time</p>
          <ul className="space-y-1">
            {series.map((point) => (
              <li key={point.day} className="grid grid-cols-[6.5rem_1fr_2rem] items-center gap-2 text-small">
                <span className="text-fg-3">{point.day.slice(5)}</span>
                <span className="h-1.5 bg-accent/80" style={{ width: `${Math.max(6, (point.count / max) * 100)}%` }} />
                <span className="text-fg-2">{point.count}</span>
              </li>
            ))}
          </ul>
        </div>
      ) : null}

      <section className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div>
          <div className="mb-3 flex flex-wrap items-end gap-2">
            <Select
              value={category}
              onValueChange={(value) => {
                setCategory(value);
                setEventType("");
              }}
              options={[{ value: "", label: "All categories" }, ...Object.entries(LABELS).map(([value, label]) => ({ value, label }))]}
              placeholder="Category"
            />
            <Select
              value={eventType}
              onValueChange={setEventType}
              options={[{ value: "", label: "All events" }, ...typeOptions.map((item) => ({ value: item.id, label: item.label }))]}
              placeholder="Event"
            />
            <div className="relative min-w-[14rem] flex-1">
              <Input
                value={search}
                onChange={(event) => {
                  const value = event.target.value;
                  setSearch(value);
                  setMemberId("");
                  void lookup(value, setSuggestions);
                }}
                placeholder="Search a member or text"
                aria-label="Search events"
              />
              {suggestions.length > 0 && !memberId ? (
                <ul className="absolute z-10 mt-1 w-full border border-line bg-bg-1">
                  {suggestions.map((member) => (
                    <li key={member.id}>
                      <button
                        type="button"
                        className="flex w-full items-center gap-2 px-2 py-1.5 text-start text-small hover:bg-bg-2"
                        onClick={() => {
                          setMemberId(member.id);
                          setSearch(member.display_name || member.username || "Member");
                          setSuggestions([]);
                        }}
                      >
                        <Avatar entity={member} />
                        <span>{member.display_name || member.username || "Member"}</span>
                      </button>
                    </li>
                  ))}
                </ul>
              ) : null}
            </div>
            <Input type="datetime-local" value={since} onChange={(event) => setSince(event.target.value)} aria-label="From" />
            <Input type="datetime-local" value={until} onChange={(event) => setUntil(event.target.value)} aria-label="Until" />
            <Button type="button" variant="secondary" onClick={() => void load()}>
              Filter
            </Button>
          </div>

          {data.events.length === 0 ? (
            <p className="text-small text-fg-3">No events match these filters.</p>
          ) : (
            <ul className="divide-y divide-line-subtle border-y border-line-subtle">
              {data.events.map((row) => {
                const shown = row.presentation;
                const who = shown?.actor || shown?.target;
                return (
                  <li key={row.id}>
                    <button
                      type="button"
                      className={`grid w-full grid-cols-[1.25rem_1.75rem_minmax(0,1fr)] items-center gap-2 px-1 py-2 text-start ${detail?.id === row.id ? "bg-bg-2" : ""}`}
                      onClick={() => setDetail(row)}
                    >
                      <EventIcon category={row.category} />
                      <Avatar entity={who} />
                      <span className="min-w-0">
                        <span className="block truncate text-small text-fg-1">{shown?.summary || shown?.title || "Server event"}</span>
                        <span className="block truncate text-caption text-fg-3">
                          {shown?.change_line ? `${shown.change_line} · ` : ""}
                          <span suppressHydrationWarning>{relativeTime(row.occurred_at)}</span>
                          {" · "}
                          {shown?.category_label || LABELS[row.category] || "Server"}
                          {shown?.channel?.name ? ` · #${shown.channel.name}` : ""}
                        </span>
                      </span>
                    </button>
                  </li>
                );
              })}
            </ul>
          )}
          {data.next_cursor ? (
            <Button type="button" variant="secondary" className="mt-3" onClick={() => void load(data.next_cursor)}>
              Older
            </Button>
          ) : null}
        </div>

        <aside className="border border-line-subtle p-3">
          {view ? (
            <div className="space-y-3">
              <div className="flex items-center gap-2">
                <Avatar entity={view.actor || view.target} />
                <div>
                  <h2 className="text-small font-medium text-fg-1">{view.title}</h2>
                  <p className="text-caption text-fg-3">{view.category_label}</p>
                </div>
              </div>
              <p className="text-small text-fg-1">{view.summary}</p>
              <dl className="space-y-2">
                {(view.changes ?? []).map((change) => (
                  <div key={`${change.label}-${change.value}`}>
                    <dt className="text-caption text-fg-3">{change.label}</dt>
                    <dd className="whitespace-pre-wrap text-small text-fg-1">{change.value}</dd>
                  </div>
                ))}
              </dl>
              {view.jump_url ? (
                <a className="text-small text-accent" href={view.jump_url} target="_blank" rel="noreferrer">
                  Jump to message
                </a>
              ) : null}
              {view.incident_id ? (
                <a className="block text-small text-accent" href={`/dashboard/guild/${guildId}/antinuke`}>
                  Related security incident
                </a>
              ) : null}
              <div className="flex flex-wrap gap-2">
                {[view.actor, view.target, view.channel].filter(Boolean).map((entity) => (
                  <button
                    key={`${entity?.id}-${personName(entity) || entity?.name}`}
                    type="button"
                    className="text-caption text-fg-3 underline-offset-2 hover:underline"
                    onClick={() => {
                      if (entity?.id) void navigator.clipboard.writeText(entity.id);
                      toast.success("ID copied");
                    }}
                  >
                    Copy ID · {personName(entity) || (entity?.name ? `#${entity.name}` : "entity")}
                  </button>
                ))}
              </div>
              <details className="text-small">
                <summary className="cursor-pointer text-fg-3">Developer details</summary>
                <pre className="mt-2 overflow-x-auto whitespace-pre-wrap text-caption text-fg-3">{JSON.stringify(detail, null, 2)}</pre>
              </details>
            </div>
          ) : (
            <p className="text-small text-fg-3">Select an event to read who did it and what changed.</p>
          )}
        </aside>
      </section>

      <section>
        <div className="mb-2 flex items-baseline justify-between gap-3">
          <h2 className="text-small font-medium text-fg-1">Routing</h2>
          <p className="text-caption text-fg-3">
            Events kept {retention.events_days} days. Message content kept {retention.message_content_days} days.
          </p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[44rem] border-collapse text-start">
            <thead>
              <tr className="border-b border-line text-caption text-fg-3">
                <th className="py-2 pe-3 text-start font-medium">Category</th>
                <th className="py-2 pe-3 text-start font-medium">Enabled</th>
                <th className="py-2 pe-3 text-start font-medium">Destination</th>
                <th className="py-2 pe-3 text-start font-medium">Delivery</th>
                <th className="py-2 text-start font-medium">Test</th>
              </tr>
            </thead>
            <tbody>
              {routes.map((row) => {
                const health = DELIVERY[row.delivery || "unchecked"] ?? DELIVERY.unchecked;
                return (
                  <tr key={row.category} className="border-b border-line-subtle">
                    <td className="py-2 pe-3 text-small">
                      {LABELS[row.category] ?? row.category}
                      {row.category === "bot_actions" ? <span className="mt-0.5 block text-caption text-fg-3">Reserved. No events are written yet.</span> : null}
                    </td>
                    <td className="py-2 pe-3">
                      <Switch
                        checked={row.enabled}
                        aria-label={`${LABELS[row.category] ?? row.category} enabled`}
                        onCheckedChange={(enabled) => void saveRoute({ ...row, enabled })}
                      />
                    </td>
                    <td className="py-2 pe-3">
                      <Select
                        value={row.channel_id ?? ""}
                        options={[{ value: "", label: "No channel" }, ...channelOptions]}
                        placeholder="Select channel"
                        onValueChange={(channelId) => void saveRoute({ ...row, channel_id: channelId || null })}
                      />
                    </td>
                    <td className="py-2 pe-3">
                      <StatusLabel status={health.status}>{health.label}</StatusLabel>
                    </td>
                    <td className="py-2">
                      <Button
                        type="button"
                        variant="secondary"
                        disabled={!row.enabled || !row.channel_id}
                        onClick={() => void sendTest(row)}
                      >
                        Send test log
                      </Button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </section>

      <section className="grid gap-4 lg:grid-cols-3">
        <IgnoreList
          label="Ignored channels"
          hint="Message events skip these channels."
          options={textChannels.map((channel) => ({ id: channel.id, label: `#${channel.name}` }))}
          selected={ignoredChannels}
          onChange={(channels) => {
            setIgnoredChannels(channels);
            void saveIgnores({ channels, roles: ignoredRoles, users: ignoredUsers });
          }}
        />
        <IgnoreList
          label="Ignored roles"
          hint="Message events skip members with these roles."
          options={roles.filter((role) => role.name !== "@everyone").map((role) => ({ id: role.id, label: `@${role.name}` }))}
          selected={ignoredRoles}
          onChange={(next) => {
            setIgnoredRoles(next);
            void saveIgnores({ channels: ignoredChannels, roles: next, users: ignoredUsers });
          }}
        />
        <div>
          <h3 className="text-small font-medium text-fg-1">Ignored members</h3>
          <p className="mb-2 text-caption text-fg-3">Message events skip these members.</p>
          <Input
            value={userQuery}
            placeholder="Search members"
            aria-label="Search members to ignore"
            onChange={(event) => {
              const value = event.target.value;
              setUserQuery(value);
              void lookup(value, setUserHits);
            }}
          />
          {userHits.length > 0 ? (
            <ul className="mt-1 border border-line-subtle">
              {userHits.map((member) => (
                <li key={member.id}>
                  <button
                    type="button"
                    className="flex w-full items-center gap-2 px-2 py-1.5 text-start text-small hover:bg-bg-2"
                    onClick={() => {
                      const next = ignoredUsers.some((user) => user.id === member.id) ? ignoredUsers : [...ignoredUsers, member];
                      setIgnoredUsers(next);
                      setUserHits([]);
                      setUserQuery("");
                      void saveIgnores({ channels: ignoredChannels, roles: ignoredRoles, users: next });
                    }}
                  >
                    <Avatar entity={member} />
                    <span>{member.display_name || member.username || "Member"}</span>
                  </button>
                </li>
              ))}
            </ul>
          ) : null}
          <ul className="mt-2 space-y-1">
            {ignoredUsers.map((user) => (
              <li key={user.id} className="flex items-center justify-between gap-2 text-small">
                <span>{user.display_name || user.username || "Unresolved member"}</span>
                <button
                  type="button"
                  className="text-caption text-fg-3"
                  onClick={() => {
                    const next = ignoredUsers.filter((item) => item.id !== user.id);
                    setIgnoredUsers(next);
                    void saveIgnores({ channels: ignoredChannels, roles: ignoredRoles, users: next });
                  }}
                >
                  Remove
                </button>
              </li>
            ))}
          </ul>
        </div>
      </section>
    </div>
  );
}

function IgnoreList({
  label,
  hint,
  options,
  selected,
  onChange,
}: {
  label: string;
  hint: string;
  options: Array<{ id: string; label: string }>;
  selected: string[];
  onChange: (ids: string[]) => void;
}) {
  return (
    <div>
      <h3 className="text-small font-medium text-fg-1">{label}</h3>
      <p className="mb-2 text-caption text-fg-3">{hint}</p>
      <ul className="max-h-40 space-y-1 overflow-y-auto">
        {options.length === 0 ? <li className="text-caption text-fg-3">None available.</li> : null}
        {options.map((option) => {
          const checked = selected.includes(option.id);
          return (
            <li key={option.id}>
              <label className="flex items-center gap-2 text-small">
                <input
                  type="checkbox"
                  checked={checked}
                  onChange={() => onChange(checked ? selected.filter((id) => id !== option.id) : [...selected, option.id])}
                />
                <span>{option.label}</span>
              </label>
            </li>
          );
        })}
      </ul>
    </div>
  );
}
