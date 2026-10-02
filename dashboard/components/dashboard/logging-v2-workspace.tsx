"use client";

import React, { useState } from "react";
import { usePathname, useRouter } from "next/navigation";
import { toast } from "sonner";
import { LoggingAppearancePanel, type Appearance } from "@/components/dashboard/logging-appearance-panel";
import { LoggingRoutingPanel } from "@/components/dashboard/logging-routing-panel";
import { PageHeader } from "@/components/dashboard/page-header";
import { DataTable } from "@/components/platform/data-table";
import { DetailsDrawer } from "@/components/platform/details-drawer";
import { HealthBadge } from "@/components/platform/health";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Select } from "@/components/ui/select";
import { api } from "@/lib/api";
import type { PageSize } from "@/lib/pagination";

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
  attribution?: string;
  source_line?: string;
  source_module?: string | null;
};
type EventRow = {
  id: string;
  category: string;
  event_type: string;
  occurred_at: string;
  actor_id?: string | null;
  target_id?: string | null;
  channel_id?: string | null;
  actor_confidence?: string;
  metadata?: Record<string, unknown>;
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
  total?: number;
  page?: number;
  pages?: number;
  page_size?: number;
  health?: { view_audit_log?: boolean | null; attribution?: string; note?: string | null; recent_failures?: string[] };
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
  event_styles: {},
  ignore_scope: "messages",
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
  if (row.presentation?.summary) return row.presentation.summary;
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

function Avatar({ entity }: { entity?: Entity | null }) {
  const name = personName(entity) || "Unknown member";
  if (entity?.avatar_url) {
    // Discord avatar hosts are not in the image allowlist.
    // eslint-disable-next-line @next/next/no-img-element
    return <img src={entity.avatar_url} alt="" draggable={false} className="size-8 rounded-full object-cover" />;
  }
  return <span className="grid size-8 place-items-center rounded-full bg-bg-2 text-caption text-fg-2">{name.slice(0, 1).toUpperCase()}</span>;
}

export function LoggingV2Workspace({
  guildId,
  initial,
  channels,
  roles,
  initialTab = "activity",
  initialError = null,
}: {
  guildId: string;
  initial: Home;
  channels: Array<{ id: string; name: string; type?: string | number }>;
  roles: Array<{ id: string; name: string; color?: number }>;
  initialTab?: string;
  initialError?: string | null;
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
  const [page, setPage] = useState(initial.page || 1);
  const [pageSize, setPageSize] = useState<PageSize>((initial.page_size as PageSize) || 25);
  const [loading, setLoading] = useState(false);
  const [loadError, setLoadError] = useState<string | null>(initialError);
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

  const load = async (nextPage = 1, nextSize: PageSize = pageSize) => {
    const params = new URLSearchParams();
    params.set("page", String(nextPage));
    params.set("page_size", String(nextSize));
    if (category) params.set("category", category);
    if (eventType) params.set("event_type", eventType);
    if (memberId) params.set("member_id", memberId);
    else if (search.trim()) params.set("q", search.trim());
    if (since) params.set("since", new Date(since).toISOString());
    if (until) params.set("until", new Date(until).toISOString());
    setLoading(true);
    setLoadError(null);
    try {
      const next = await api.getLoggingV2(guildId, `?${params.toString()}`);
      setData(next);
      setRoutes(next.routes ?? []);
      setEventRoutes(next.event_routes ?? []);
      setPage(next.page || nextPage);
      setPageSize(nextSize);
      if (next.appearance) setAppearance(next.appearance);
      setDetail(null);
      router.replace(`${pathname}?${params.toString()}`);
    } catch (error) {
      setLoadError(error instanceof Error ? error.message : "Logging could not be loaded");
    } finally {
      setLoading(false);
    }
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

      {tab === "activity" && data.health?.note ? (
        <p className="flex items-center gap-2 text-small text-fg-2" role="status">
          <HealthBadge status="warning" />
          <span>{data.health.note}</span>
        </p>
      ) : null}
      {tab === "activity" && data.health?.recent_failures?.length ? (
        <p className="text-small text-fg-2" role="status">Delivery issue · {data.health.recent_failures[0]}</p>
      ) : null}

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
          page={page}
          pages={data.pages || 1}
          pageSize={pageSize}
          total={data.total || data.events.length}
          loading={loading}
          error={loadError}
          guildId={guildId}
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
                return saved.mode === "inherit" && !saved.kept ? rest : [...rest, saved];
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
          ignoreScope={appearance.ignore_scope || "messages"}
          onIgnoreScope={(scope) => {
            setAppearance((current) => ({ ...current, ignore_scope: scope }));
            void api.updateLoggingAppearance(guildId, { ignore_scope: scope }).then(setAppearance).catch((error) => {
              toast.error(error instanceof Error ? error.message : "Could not save exclusions");
            });
          }}
        />
      ) : null}

      {tab === "appearance" ? (
        <LoggingAppearancePanel
          appearance={appearance}
          onChange={async (patch) => {
            setAppearance((current) => ({
              ...current,
              ...patch,
              colors: patch.colors ? { ...current.colors, ...patch.colors } : current.colors,
              event_styles: patch.event_styles ? { ...current.event_styles, ...patch.event_styles } : current.event_styles,
            }));
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
  load: (page?: number, pageSize?: PageSize) => Promise<void>;
  page: number;
  pages: number;
  pageSize: PageSize;
  total: number;
  loading: boolean;
  error: string | null;
  guildId: string;
  clearFilters: () => void;
}) {
  const { data, detail, setDetail } = props;
  return (
    <section className="grid min-w-0 items-start gap-4 lg:grid-cols-[minmax(0,1fr)_22rem]">
      <div className="min-w-0">
        <div className="mb-3 flex max-w-full flex-wrap items-center gap-2">
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
          <Button type="button" variant="secondary" onClick={() => void props.load(1, props.pageSize)}>Filter</Button>
          <Button type="button" variant="secondary" onClick={() => void exportEvents(props.guildId, props.category, props.eventType, props.memberId, props.search)}>Export JSON</Button>
        </div>
        <DataTable
          rows={props.error ? [] : data.events}
          columns={[
            {
              key: "what",
              header: "What happened",
              cell: (row) => (
                <span className="flex items-start gap-2">
                  <Avatar entity={row.presentation?.target || row.presentation?.actor} />
                  <span className="min-w-0">
                    <span className="block truncate text-fg-1">{headline(row)}</span>
                    <span className="block truncate text-caption text-fg-3">{row.presentation?.change_line}</span>
                  </span>
                </span>
              ),
            },
            {
              key: "who",
              header: "Who",
              cell: (row) => <span className="text-fg-2">{row.presentation?.source_line || personName(row.presentation?.actor) || "Actor unknown"}</span>,
            },
            {
              key: "when",
              header: "When",
              cell: (row) => <span className="text-fg-3" suppressHydrationWarning>{relativeTime(row.occurred_at)}</span>,
            },
          ]}
          getRowId={(row) => row.id}
          page={props.page}
          pages={props.pages}
          pageSize={props.pageSize}
          total={props.total}
          loading={props.loading}
          error={props.error}
          onRetry={() => void props.load(props.page, props.pageSize)}
          onPageChange={(next) => void props.load(next, props.pageSize)}
          onPageSizeChange={(size) => void props.load(1, size)}
          selectedId={detail?.id}
          onSelect={(id) => setDetail(data.events.find((row) => row.id === id) || null)}
          emptyTitle="No events"
          emptyDescription="No events match these filters."
        />
      </div>
      <EventDrawer detail={detail} onClose={() => setDetail(null)} />
    </section>
  );
}

async function exportEvents(guildId: string, category: string, eventType: string, memberId: string, search: string) {
  const params = new URLSearchParams();
  if (category) params.set("category", category);
  if (eventType) params.set("event_type", eventType);
  if (memberId) params.set("member_id", memberId);
  else if (search.trim()) params.set("q", search.trim());
  const payload = await api.getLoggingV2(guildId, `/export${params.size ? `?${params.toString()}` : ""}`);
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "logging-events.json";
  link.click();
  URL.revokeObjectURL(url);
}

function EventDrawer({ detail, onClose }: { detail: EventRow | null; onClose: () => void }) {
  const view = detail?.presentation;
  const changes = (view?.changes ?? []).filter((change) => change.label !== "Jump to message");
  const copy = (value: string) => void navigator.clipboard.writeText(value);
  return (
    <DetailsDrawer
      open={Boolean(detail)}
      onOpenChange={(open) => { if (!open) onClose(); }}
      title={detail ? headline(detail) : "Event"}
      summary={null}
      sections={detail ? [
        {
          id: "summary",
          label: "Summary",
          content: (
            <div className="space-y-2">
              <div className="flex items-center gap-2">
                <Avatar entity={view?.target || view?.actor} />
                <div>
                  <p className="text-fg-1">{subjectOf(detail)}</p>
                  <p className="text-caption text-fg-3" suppressHydrationWarning>{relativeTime(detail.occurred_at)}</p>
                </div>
              </div>
              <p className="text-fg-1">{view?.summary}</p>
              <p className="text-caption text-fg-3">{view?.source_line}</p>
            </div>
          ),
        },
        {
          id: "changes",
          label: "Changes",
          content: changes.length ? (
            <div className="space-y-2">
              {changes.map((change) => (
                <div key={`${change.label}-${change.value}`}>
                  <p className="text-caption text-fg-3">{change.label}</p>
                  <p className="whitespace-pre-wrap text-fg-1">{change.value}</p>
                </div>
              ))}
            </div>
          ) : <p className="text-fg-3">No field changes were captured.</p>,
        },
        {
          id: "attribution",
          label: "Attribution",
          content: (
            <div className="space-y-1">
              <p className="text-fg-1">{view?.attribution || "Unknown"}</p>
              <p className="text-fg-2">{view?.source_line}</p>
              <p className="text-caption text-fg-3">{personName(view?.actor) || "No actor was recorded."}</p>
            </div>
          ),
        },
        {
          id: "context",
          label: "Related context",
          content: (
            <div className="space-y-1">
              <p>{view?.channel?.name ? `#${view.channel.name}` : "No channel"}</p>
              <p>{view?.target?.name || personName(view?.target) || "No target name"}</p>
              {view?.jump_url ? <a className="underline" href={view.jump_url} target="_blank" rel="noreferrer">View message</a> : null}
            </div>
          ),
        },
        {
          id: "developer",
          label: "Developer",
          content: (
            <div className="space-y-2">
              {[
                ["Event ID", detail.id],
                ["Audit entry", String((detail.metadata || {}).audit_entry_id || "—")],
                ["Guild", "this server"],
                ["Channel", detail.channel_id || "—"],
                ["Member", detail.target_id || detail.actor_id || "—"],
              ].map(([label, value]) => (
                <div key={label} className="flex items-center justify-between gap-2">
                  <span className="text-fg-3">{label}</span>
                  <span className="font-mono text-caption" dir="ltr">{value}</span>
                  <Button type="button" variant="secondary" onClick={() => copy(String(value))}>Copy</Button>
                </div>
              ))}
              <Button type="button" variant="secondary" onClick={() => copy(JSON.stringify(detail, null, 2))}>Copy JSON</Button>
              <pre className="overflow-auto border border-line bg-surface-well p-2 text-caption" dir="ltr">{JSON.stringify(detail, null, 2)}</pre>
            </div>
          ),
        },
      ] : undefined}
    />
  );
}
