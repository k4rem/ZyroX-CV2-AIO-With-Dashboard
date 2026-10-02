"use client";

import React, { useEffect, useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { Hash, MessageSquare, Mic, Settings, Shield, UserRound } from "lucide-react";
import { toast } from "sonner";
import { LoggingAppearancePanel, type Appearance } from "@/components/dashboard/logging-appearance-panel";
import { LoggingRoutingPanel } from "@/components/dashboard/logging-routing-panel";
import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import { Dialog, DialogBody, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Select } from "@/components/ui/select";
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
  automod: "Automod",
  security: "Security",
};

const EVENT_TITLES: Record<string, string> = {
  message_edit: "Message edited",
  message_delete: "Message deleted",
  message_bulk_delete: "Messages deleted",
  member_join: "Member joined",
  member_leave: "Member left",
  member_kick: "Member kicked",
  member_ban: "Member banned",
  member_unban: "Member unbanned",
  member_timeout: "Timeout added",
  member_timeout_removed: "Timeout removed",
  member_nickname: "Nickname changed",
  member_roles: "Member roles updated",
  role_create: "Role created",
  role_update: "Role updated",
  role_delete: "Role deleted",
  channel_create: "Channel created",
  channel_update: "Channel updated",
  channel_delete: "Channel deleted",
  voice_join: "Member joined voice",
  voice_leave: "Left voice",
  voice_move: "Moved voice channel",
  guild_update: "Server settings updated",
  logging_test: "Logging test",
};

type Entity = { id?: string; display_name?: string | null; username?: string | null; name?: string | null; avatar_url?: string | null; color?: string | null };
type Presentation = {
  title?: string;
  summary?: string;
  change_line?: string;
  category_label?: string;
  actor?: Entity | null;
  target?: Entity | null;
  channel?: Entity | null;
  changes?: Array<{ label: string; value: string }>;
  jump_url?: string | null;
  identifiers?: string[];
};
type EventRow = {
  id: string;
  category: string;
  event_type: string;
  occurred_at: string;
  before?: { content?: string; roles?: Entity[] } | null;
  after?: { content?: string; roles?: Entity[] } | null;
  presentation?: Presentation;
};
type RouteRow = { category: string; enabled: boolean; channel_id: string | null; channel_name?: string | null; delivery?: string };
type IgnoreUser = { id: string; display_name?: string | null; username?: string | null; avatar_url?: string | null };
type Home = {
  routes: RouteRow[];
  events: EventRow[];
  next_cursor: string | null;
  event_types?: Array<{ id: string; label: string; category: string }>;
  groups?: Array<{ category: string; label: string; events: Array<{ id: string; label: string }> }>;
  event_routes?: Array<{ event_type: string; mode: string; channel_id: string | null }>;
  appearance?: Appearance;
  ignores?: { channels: Array<{ id: string }>; roles: Array<{ id: string }>; users: IgnoreUser[] };
};

const DEFAULT_APPEARANCE: Appearance = {
  style: "balanced",
  show_avatars: true,
  show_moderator: true,
  show_jump: true,
  show_timestamp: true,
  show_ids: false,
  footer_mode: "cls",
  footer_text: null,
  colors: {},
};

function eventTitle(row: EventRow) {
  return row.presentation?.title || EVENT_TITLES[row.event_type] || "Logged event";
}

function personName(entity?: Entity | null) {
  return entity?.display_name || entity?.username || entity?.name || null;
}

function subjectOf(row: EventRow) {
  const view = row.presentation;
  const named = personName(view?.target) || personName(view?.actor);
  if (named) return named;
  if (row.event_type.startsWith("channel") || row.event_type.startsWith("guild") || row.event_type.startsWith("role_")) {
    return view?.channel?.name ? `#${view.channel.name}` : view?.target?.name || "This server";
  }
  return "Unknown member";
}

function headline(row: EventRow) {
  const name = subjectOf(row);
  const type = row.event_type;
  if (type === "message_edit") return `${name} edited a message`;
  if (type === "message_delete") return `${name}'s message was deleted`;
  if (type === "message_bulk_delete") return "Messages were deleted";
  if (type === "member_roles") return `${name}'s roles changed`;
  if (type === "member_join") return `${name} joined`;
  if (type === "member_leave") return `${name} left`;
  if (type === "member_kick") return `${name} was kicked`;
  if (type === "member_ban") return `${name} was banned`;
  if (type === "voice_join") return `${name} joined voice`;
  if (type === "voice_leave") return `${name} left voice`;
  if (type === "voice_move") return `${name} moved voice channels`;
  return eventTitle(row);
}

function relativeTime(iso: string) {
  const minutes = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (Number.isNaN(minutes)) return "";
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.round(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  return `${Math.round(hours / 24)}d ago`;
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
  const name = personName(entity) || "Unknown member";
  if (entity?.avatar_url) {
    // Discord avatar hosts are not in the image allowlist.
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={entity.avatar_url} alt="" className="size-8 rounded-full object-cover" />;
  }
  return <span className="grid size-8 place-items-center rounded-full bg-bg-2 text-caption text-fg-2">{name.slice(0, 1).toUpperCase()}</span>;
}

export function LoggingV2Workspace({
  guildId,
  initial,
  channels,
  roles,
  initialTab = "activity",
}: {
  guildId: string;
  initial: Home;
  channels: Array<{ id: string; name: string; type?: string | number }>;
  roles: Array<{ id: string; name: string; color?: number }>;
  initialTab?: string;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const starting = initialTab === "routing" || initialTab === "appearance" ? initialTab : "activity";
  const [tab, setTab] = useState(starting);
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
  const [eventRoutes, setEventRoutes] = useState(initial.event_routes ?? []);
  const [appearance, setAppearance] = useState<Appearance>(initial.appearance ?? DEFAULT_APPEARANCE);
  const [ignoredChannels, setIgnoredChannels] = useState((initial.ignores?.channels ?? []).map((item) => item.id));
  const [ignoredRoles, setIgnoredRoles] = useState((initial.ignores?.roles ?? []).map((item) => item.id));
  const [ignoredUsers, setIgnoredUsers] = useState<IgnoreUser[]>(initial.ignores?.users ?? []);

  const typeOptions = (data.event_types ?? []).filter((item) => !category || item.category === category);
  const dateLabel = since || until ? "Date set" : "Date";

  const openTab = (next: string) => {
    setTab(next);
    router.replace(next === "activity" ? pathname : `${pathname}?tab=${next}`);
  };

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
    setEventRoutes(next.event_routes ?? []);
    if (next.appearance) setAppearance(next.appearance);
    setDetail(null);
  };

  const lookup = async (value: string) => {
    if (value.trim().length < 2) {
      setSuggestions([]);
      return;
    }
    try {
      const result = await api.searchLoggingMembers(guildId, value.trim());
      setSuggestions(result.members ?? []);
    } catch {
      setSuggestions([]);
    }
  };

  return (
    <div className="space-y-4">
      <PageHeader title="Logging" description="Server activity, where it is delivered, and how the Discord log looks." />
      <div className="flex gap-4 border-b border-line">
        {(
          [
            ["activity", "Activity"],
            ["routing", "Routing"],
            ["appearance", "Appearance"],
          ] as const
        ).map(([id, label]) => (
          <button
            key={id}
            type="button"
            className={`-mb-px border-b-2 pb-2 text-small ${tab === id ? "border-brand-400 text-fg-1" : "border-transparent text-fg-3"}`}
            onClick={() => openTab(id)}
          >
            {label}
          </button>
        ))}
      </div>

      {tab === "activity" ? (
        <Activity
          data={data}
          detail={detail}
          setDetail={setDetail}
          category={category}
          setCategory={setCategory}
          eventType={eventType}
          setEventType={setEventType}
          typeOptions={typeOptions}
          search={search}
          setSearch={setSearch}
          memberId={memberId}
          setMemberId={setMemberId}
          suggestions={suggestions}
          lookup={lookup}
          since={since}
          until={until}
          setSince={setSince}
          setUntil={setUntil}
          dateLabel={dateLabel}
          load={load}
          clearFilters={() => {
            setCategory("");
            setEventType("");
            setSearch("");
            setMemberId("");
            setSince("");
            setUntil("");
          }}
        />
      ) : null}

      {tab === "routing" ? (
        <LoggingRoutingPanel
          routes={routes}
          groups={data.groups ?? []}
          eventRoutes={eventRoutes}
          channels={channels}
          roles={roles}
          ignoredChannels={ignoredChannels}
          ignoredRoles={ignoredRoles}
          ignoredUsers={ignoredUsers}
          onRoute={async (row) => {
            try {
              const saved = await api.updateLoggingRoute(guildId, { category: row.category, enabled: row.enabled, channel_id: row.channel_id });
              setRoutes((current) => current.map((item) => (item.category === row.category ? { ...item, ...saved } : item)));
            } catch (error) {
              toast.error(error instanceof Error ? error.message : "Could not save the route");
            }
          }}
          onEventRoute={async (eventType, mode, channelId) => {
            try {
              const saved = await api.updateLoggingEventRoute(guildId, eventType, { mode, channel_id: channelId });
              setEventRoutes((current) => {
                const rest = current.filter((item) => item.event_type !== eventType);
                return saved.mode === "inherit" ? rest : [...rest, saved];
              });
            } catch (error) {
              toast.error(error instanceof Error ? error.message : "Could not save the event route");
            }
          }}
          onTest={async (category) => {
            try {
              const saved = await api.sendLoggingTest(guildId, category);
              if (saved.route) setRoutes((current) => current.map((item) => (item.category === category ? { ...item, ...saved.route } : item)));
              toast.success("Test log sent");
            } catch (error) {
              toast.error(error instanceof Error ? error.message : "Could not send the test log");
            }
          }}
          onEventTest={async (eventType) => {
            try {
              await api.sendLoggingEventTest(guildId, eventType);
              toast.success("Test log sent");
            } catch (error) {
              toast.error(error instanceof Error ? error.message : "Could not send the test log");
            }
          }}
          onIgnores={async (next) => {
            try {
              const saved = await api.updateLoggingIgnores(guildId, {
                channels: next.channels,
                roles: next.roles,
                users: next.users.map((user) => user.id),
              });
              setIgnoredChannels((saved.channels ?? []).map((item: { id: string }) => item.id));
              setIgnoredRoles((saved.roles ?? []).map((item: { id: string }) => item.id));
              setIgnoredUsers(saved.users ?? []);
            } catch (error) {
              toast.error(error instanceof Error ? error.message : "Could not save exclusions");
            }
          }}
          onSearchMembers={async (query) => (await api.searchLoggingMembers(guildId, query)).members ?? []}
        />
      ) : null}

      {tab === "appearance" ? (
        <LoggingAppearancePanel
          appearance={appearance}
          onChange={async (patch) => {
            setAppearance((current) => ({ ...current, ...patch, colors: patch.colors ? { ...current.colors, ...patch.colors } : current.colors }));
            try {
              const saved = await api.updateLoggingAppearance(guildId, patch);
              setAppearance(saved);
            } catch (error) {
              toast.error(error instanceof Error ? error.message : "Could not save appearance");
            }
          }}
        />
      ) : null}
    </div>
  );
}

function Activity(props: {
  data: Home;
  detail: EventRow | null;
  setDetail: (row: EventRow | null) => void;
  category: string;
  setCategory: (value: string) => void;
  eventType: string;
  setEventType: (value: string) => void;
  typeOptions: Array<{ id: string; label: string }>;
  search: string;
  setSearch: (value: string) => void;
  memberId: string;
  setMemberId: (value: string) => void;
  suggestions: IgnoreUser[];
  lookup: (value: string) => void;
  since: string;
  until: string;
  setSince: (value: string) => void;
  setUntil: (value: string) => void;
  dateLabel: string;
  load: (cursor?: string | null) => Promise<void>;
  clearFilters: () => void;
}) {
  const { data, detail, setDetail } = props;
  return (
    <section className="grid items-start gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
      <div>
        <div className="mb-3 flex flex-wrap items-center gap-2">
          <Select className="w-40" value={props.category} onValueChange={(value) => { props.setCategory(value); props.setEventType(""); }} options={[{ value: "", label: "All categories" }, ...Object.entries(LABELS).map(([value, label]) => ({ value, label }))]} placeholder="Category" />
          <Select className="w-44" value={props.eventType} onValueChange={props.setEventType} options={[{ value: "", label: "All events" }, ...props.typeOptions.map((item) => ({ value: item.id, label: item.label }))]} placeholder="Event" />
          <div className="relative w-52">
            <Input
              value={props.search}
              placeholder="Search member or text"
              aria-label="Search events"
              onChange={(event) => {
                props.setSearch(event.target.value);
                props.setMemberId("");
                props.lookup(event.target.value);
              }}
            />
            {props.suggestions.length > 0 && !props.memberId ? (
              <ul className="absolute z-10 mt-1 w-full border border-line bg-bg-1">
                {props.suggestions.map((member) => (
                  <li key={member.id}>
                    <button type="button" className="block w-full px-2 py-1.5 text-start text-small hover:bg-bg-2" onClick={() => { props.setMemberId(member.id); props.setSearch(member.display_name || member.username || "Member"); }}>
                      {member.display_name || member.username || "Member"}
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
          <Popover>
            <PopoverTrigger asChild>
              <Button type="button" variant="secondary">{props.dateLabel}</Button>
            </PopoverTrigger>
            <PopoverContent className="space-y-2 p-3">
              <Input type="datetime-local" value={props.since} onChange={(event) => props.setSince(event.target.value)} aria-label="From" />
              <Input type="datetime-local" value={props.until} onChange={(event) => props.setUntil(event.target.value)} aria-label="Until" />
              <Button type="button" variant="secondary" onClick={() => void props.load()}>Apply</Button>
            </PopoverContent>
          </Popover>
          <Popover>
            <PopoverTrigger asChild>
              <Button type="button" variant="secondary">More filters</Button>
            </PopoverTrigger>
            <PopoverContent className="p-3">
              <p className="mb-2 text-caption text-fg-3">Search matches a member or text in the event.</p>
              <Button type="button" variant="secondary" onClick={props.clearFilters}>Clear filters</Button>
            </PopoverContent>
          </Popover>
          <Button type="button" variant="secondary" onClick={() => void props.load()}>Filter</Button>
        </div>
        {data.events.length === 0 ? (
          <p className="text-small text-fg-3">No events match these filters.</p>
        ) : (
          <ul className="divide-y divide-line-subtle border-y border-line-subtle">
            {data.events.map((row) => {
              const shown = row.presentation;
              const who = shown?.target || shown?.actor;
              const actor = personName(shown?.actor);
              const same = shown?.actor?.id && shown.actor.id === shown?.target?.id;
              const channel = shown?.channel?.name ? `#${shown.channel.name}` : null;
              const meta = row.event_type.startsWith("message")
                ? [channel, relativeTime(row.occurred_at)]
                : [actor && !same ? `by ${actor}` : null, channel, relativeTime(row.occurred_at)];
              const selected = detail?.id === row.id;
              return (
                <li key={row.id}>
                  <button
                    type="button"
                    className={`grid w-full grid-cols-[2rem_minmax(0,1fr)] items-start gap-2 px-1 py-2 text-start ${selected ? "border-s-2 border-brand-400 bg-bg-2" : ""}`}
                    onClick={() => setDetail(row)}
                  >
                    <Avatar entity={who} />
                    <span className="min-w-0">
                      <span className="flex items-center gap-1.5">
                        <EventIcon category={row.category} />
                        <span className="truncate text-small text-fg-1">{headline(row)}</span>
                      </span>
                      <span className="block truncate text-caption text-fg-3" suppressHydrationWarning>{meta.filter(Boolean).join(" · ")}</span>
                      {shown?.change_line ? <span className="mt-0.5 block truncate text-caption text-fg-1">{shown.change_line}</span> : null}
                    </span>
                  </button>
                </li>
              );
            })}
          </ul>
        )}
        {data.next_cursor ? (
          <Button type="button" variant="secondary" className="mt-3" onClick={() => void props.load(data.next_cursor)}>Older</Button>
        ) : null}
      </div>
      <Detail detail={detail} onClose={() => setDetail(null)} />
    </section>
  );
}

function useNarrow() {
  const [narrow, setNarrow] = useState(false);
  useEffect(() => {
    const query = window.matchMedia("(max-width: 1023px)");
    const apply = () => setNarrow(query.matches);
    apply();
    query.addEventListener("change", apply);
    return () => query.removeEventListener("change", apply);
  }, []);
  return narrow;
}

function Detail({ detail, onClose }: { detail: EventRow | null; onClose: () => void }) {
  const narrow = useNarrow();
  const panel = detail ? <DetailBody detail={detail} /> : <p className="text-small text-fg-3">Select an event.</p>;
  if (narrow) {
    return (
      <Dialog open={Boolean(detail)} onOpenChange={(open) => { if (!open) onClose(); }}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Event</DialogTitle>
          </DialogHeader>
          <DialogBody>{detail ? <DetailBody detail={detail} /> : null}</DialogBody>
        </DialogContent>
      </Dialog>
    );
  }
  return <aside className="border border-line-subtle p-3">{panel}</aside>;
}

function DetailBody({ detail }: { detail: EventRow }) {
  const view = detail.presentation;
  const who = view?.target || view?.actor;
  const added = (view?.changes ?? []).find((change) => change.label === "Roles added");
  const removed = (view?.changes ?? []).find((change) => change.label === "Roles removed");
  const before = detail.before?.content;
  const after = detail.after?.content;
  const message = detail.event_type === "message_edit" || detail.event_type === "message_delete";
  return (
    <div className="space-y-3">
      <div className="flex items-center gap-2">
        <Avatar entity={who} />
        <div className="min-w-0">
          <h2 className="truncate text-small font-medium text-fg-1">{subjectOf(detail)}</h2>
          <p className="text-small text-fg-2">{eventTitle(detail)}</p>
          <p className="text-caption text-fg-3" suppressHydrationWarning>
            {view?.channel?.name ? `#${view.channel.name} · ` : ""}
            {relativeTime(detail.occurred_at)}
          </p>
        </div>
      </div>
      {message ? (
        <div className="space-y-2">
          {before !== undefined ? (
            <div>
              <p className="text-caption text-fg-3">Before</p>
              <p className="whitespace-pre-wrap text-small text-fg-1">{before || "—"}</p>
            </div>
          ) : null}
          {after !== undefined ? (
            <div>
              <p className="text-caption text-fg-3">After</p>
              <p className="whitespace-pre-wrap text-small text-fg-1">{after || "—"}</p>
            </div>
          ) : null}
          {view?.jump_url ? (
            <a className="inline-block border border-line px-2 py-1 text-caption text-fg-1" href={view.jump_url} target="_blank" rel="noreferrer">
              View message
            </a>
          ) : null}
        </div>
      ) : null}
      {added || removed ? (
        <div className="space-y-2">
          {added ? <Chips label="Roles added" value={added.value} /> : null}
          {removed ? <Chips label="Roles removed" value={removed.value} /> : null}
        </div>
      ) : null}
      {(view?.changes ?? [])
        .filter((change) => !["Roles added", "Roles removed", "Before", "After", "Jump to message"].includes(change.label))
        .map((change) => (
          <div key={`${change.label}-${change.value}`}>
            <p className="text-caption text-fg-3">{change.label}</p>
            <p className="whitespace-pre-wrap text-small text-fg-1">{change.value}</p>
          </div>
        ))}
      <details className="text-small">
        <summary className="cursor-pointer text-fg-3">Developer details</summary>
        <div className="mt-2 space-y-1">
          {(view?.identifiers ?? []).map((item) => (
            <p key={item} className="text-caption text-fg-3">{item}</p>
          ))}
          <p className="text-caption text-fg-3">{detail.event_type}</p>
          <pre className="overflow-x-auto whitespace-pre-wrap text-caption text-fg-3">{JSON.stringify(detail, null, 2)}</pre>
        </div>
      </details>
    </div>
  );
}

function Chips({ label, value }: { label: string; value: string }) {
  const names = value.split(",").map((item) => item.trim()).filter((item) => item && item !== "—");
  return (
    <div>
      <p className="text-caption text-fg-3">{label}</p>
      <div className="mt-1 flex flex-wrap gap-1">
        {names.map((name) => (
          <span key={name} className="border border-line px-1.5 py-0.5 text-caption text-fg-1">{name}</span>
        ))}
      </div>
    </div>
  );
}
