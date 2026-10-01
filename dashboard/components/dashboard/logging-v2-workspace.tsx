"use client";

import React, { useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { SettingGroup } from "@/components/settings/setting-group";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Readout } from "@/components/ui/readout";
import { Select } from "@/components/ui/select";
import { StatusLabel } from "@/components/ui/status";
import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api";

const LABELS: Record<string, string> = {
  message_events: "Message events",
  join_leave_events: "Join and leave",
  member_moderation: "Moderation",
  voice_events: "Voice",
  role_events: "Roles",
  channel_events: "Channels",
  guild_events: "Server",
  bot_actions: "Bot actions",
};

type EventRow = {
  id: string;
  category: string;
  event_type: string;
  occurred_at: string;
  actor_id: string | null;
  actor_confidence: string;
  target_id: string | null;
  channel_id: string | null;
  before: Record<string, unknown> | null;
  after: Record<string, unknown> | null;
  metadata: Record<string, unknown>;
};

type Home = {
  overview: {
    total: number;
    by_category: Record<string, number>;
    top_types: Array<{ event_type: string; count: number }>;
    series: Array<{ day: string; count: number }>;
    heatmap: Array<{ weekday: number; hour: number; count: number }> | null;
  };
  routes: Array<{ category: string; enabled: boolean; channel_id: string | null }>;
  events: EventRow[];
  next_cursor: string | null;
};

export function LoggingV2Workspace({
  guildId,
  initial,
  channels,
}: {
  guildId: string;
  initial: Home;
  channels: Array<{ id: string; name: string }>;
}) {
  const [data, setData] = useState(initial);
  const [category, setCategory] = useState("");
  const [actor, setActor] = useState("");
  const [target, setTarget] = useState("");
  const [since, setSince] = useState("");
  const [detail, setDetail] = useState<EventRow | null>(null);
  const [routes, setRoutes] = useState(initial.routes);

  const load = async (cursor?: string | null) => {
    const params = new URLSearchParams();
    if (category) params.set("category", category);
    if (actor) params.set("actor_id", actor);
    if (target) params.set("target_id", target);
    if (since) params.set("since", new Date(since).toISOString());
    if (cursor) params.set("cursor", cursor);
    const next = await api.getLoggingV2(guildId, params.size ? `?${params.toString()}` : "");
    setData(next);
    setRoutes(next.routes);
  };

  const saveRoute = async (item: { category: string; enabled: boolean; channel_id: string | null }) => {
    await api.updateLoggingRoute(guildId, item);
    setRoutes((current) => current.map((row) => (row.category === item.category ? item : row)));
    toast.success("Route saved");
  };

  const max = Math.max(1, ...data.overview.series.map((point) => point.count));
  const channelOptions = channels.map((channel) => ({ value: channel.id, label: channel.name }));

  return (
    <div className="space-y-6">
      <PageHeader title="Logging" description="Stored server events, filters, and channel routing." />
      <dl className="grid grid-cols-3 border border-line-subtle">
        <Readout label="Stored events">{data.overview.total}</Readout>
        <Readout label="Categories">{Object.keys(data.overview.by_category).length}</Readout>
        <Readout label="Routed">{routes.filter((row) => row.enabled && row.channel_id).length}</Readout>
      </dl>

      {data.overview.total === 0 ? (
        <p className="text-small text-fg-3">No stored events yet. Counts and charts appear after the bot records activity.</p>
      ) : (
        <div className="grid gap-4 lg:grid-cols-3">
          <SettingGroup id="log-series" label="Events over time">
            <ul className="space-y-2">
              {data.overview.series.map((point) => (
                <li key={point.day} className="grid grid-cols-[6.5rem_1fr_2rem] items-center gap-2 text-small">
                  <span className="font-mono text-fg-3">{point.day}</span>
                  <span className="h-2 bg-accent" style={{ width: `${Math.max(8, (point.count / max) * 100)}%` }} />
                  <span className="font-mono text-fg-1">{point.count}</span>
                </li>
              ))}
            </ul>
          </SettingGroup>
          <SettingGroup id="log-categories" label="Categories">
            <ul className="space-y-1 text-small">
              {Object.entries(data.overview.by_category).map(([name, count]) => (
                <li key={name} className="flex justify-between gap-3">
                  <span>{LABELS[name] ?? name}</span>
                  <span className="font-mono">{count}</span>
                </li>
              ))}
            </ul>
          </SettingGroup>
          <SettingGroup id="log-types" label="Top event types">
            <ul className="space-y-1 text-small">
              {data.overview.top_types.map((row) => (
                <li key={row.event_type} className="flex justify-between gap-3">
                  <span className="font-mono">{row.event_type}</span>
                  <span className="font-mono">{row.count}</span>
                </li>
              ))}
            </ul>
          </SettingGroup>
        </div>
      )}

      {data.overview.heatmap ? (
        <SettingGroup id="log-heatmap" label="Activity by hour">
          <p className="text-small text-fg-3">{data.overview.heatmap.length} occupied hour cells from stored history.</p>
        </SettingGroup>
      ) : data.overview.total > 0 ? (
        <p className="text-small text-fg-3">Not enough history for an activity heatmap. Seven days of stored events are required.</p>
      ) : null}

      <SettingGroup id="log-stream" label="Event stream">
        <div className="flex flex-wrap gap-2">
          <Select value={category} onValueChange={setCategory} options={[{ value: "", label: "All categories" }, ...Object.entries(LABELS).map(([value, label]) => ({ value, label }))]} placeholder="Category" />
          <Input value={actor} onChange={(event) => setActor(event.target.value)} placeholder="Actor ID" />
          <Input value={target} onChange={(event) => setTarget(event.target.value)} placeholder="Target ID" />
          <Input type="datetime-local" value={since} onChange={(event) => setSince(event.target.value)} />
          <Button type="button" variant="secondary" onClick={() => void load()}>Filter</Button>
        </div>
        {data.events.length === 0 ? (
          <p className="text-small text-fg-3">No events match these filters.</p>
        ) : (
          <ul className="divide-y divide-line-subtle">
            {data.events.map((row) => (
              <li key={row.id}>
                <button type="button" className="grid w-full grid-cols-1 gap-1 py-2 text-left text-small md:grid-cols-[8rem_1fr_1fr]" onClick={() => setDetail(row)}>
                  <span className="font-mono text-fg-3">{row.occurred_at.slice(0, 16)}</span>
                  <span>{LABELS[row.category] ?? row.category} · {row.event_type}</span>
                  <span className="font-mono text-fg-3">{row.actor_id ?? "unknown"} → {row.target_id ?? "—"}</span>
                </button>
              </li>
            ))}
          </ul>
        )}
        {data.next_cursor ? (
          <Button type="button" variant="secondary" onClick={() => void load(data.next_cursor)}>Older</Button>
        ) : null}
      </SettingGroup>

      <SettingGroup id="log-detail" label="Event detail">
        {detail ? (
          <pre className="overflow-x-auto whitespace-pre-wrap text-small text-fg-1">{JSON.stringify(detail, null, 2)}</pre>
        ) : (
          <p className="text-small text-fg-3">Select an event to read actor, target, and before/after.</p>
        )}
      </SettingGroup>

      <SettingGroup id="log-routes" label="Routing">
        <div className="overflow-x-auto">
          <table className="w-full min-w-[36rem] border-collapse text-start">
            <thead>
              <tr className="border-b border-line text-caption text-fg-3">
                <th className="py-2 pe-3 text-start font-medium">Category</th>
                <th className="py-2 pe-3 text-start font-medium">Enabled</th>
                <th className="py-2 text-start font-medium">Channel</th>
              </tr>
            </thead>
            <tbody>
              {routes.map((row) => (
                <tr key={row.category} className="border-b border-line-subtle">
                  <td className="py-2 pe-3">{LABELS[row.category] ?? row.category}</td>
                  <td className="py-2 pe-3">
                    <Switch
                      checked={row.enabled}
                      aria-label={`${LABELS[row.category] ?? row.category} enabled`}
                      onCheckedChange={(enabled) => void saveRoute({ ...row, enabled })}
                    />
                  </td>
                  <td className="py-2">
                    <div className="flex items-center gap-2">
                      <Select
                        value={row.channel_id ?? ""}
                        options={channelOptions}
                        placeholder="Select channel"
                        onValueChange={(channelId) => void saveRoute({ ...row, channel_id: channelId || null })}
                      />
                      <StatusLabel status={row.enabled && row.channel_id ? "healthy" : row.enabled ? "warning" : "disabled"}>
                        {row.enabled && row.channel_id ? "Routed" : row.enabled ? "Incomplete" : "Off"}
                      </StatusLabel>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </SettingGroup>
    </div>
  );
}
