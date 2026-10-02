"use client";

import React, { useCallback, useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { ChannelPicker, RolePicker, type ChannelOption } from "@/components/discord/channel-picker";
import { DiscordMessagePreview } from "@/components/discord/message-preview";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { StatusLabel } from "@/components/ui/status";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { filterGiveaways, giveawayPreview, type GiveawayRow, type GiveawayView } from "@/lib/giveaways";

const DURATIONS = [
  { value: "10", label: "10 minutes" },
  { value: "60", label: "1 hour" },
  { value: "1440", label: "1 day" },
  { value: "custom", label: "Custom end" },
];

function statusOf(status: string): "pending" | "healthy" | "disabled" | "unknown" {
  if (status === "scheduled") return "pending";
  if (status === "open") return "healthy";
  if (status === "ended") return "disabled";
  return "unknown";
}

function statusText(status: string) {
  if (status === "open") return "Live";
  if (status === "scheduled") return "Scheduled";
  if (status === "ended") return "Ended";
  return "Archived";
}

function localInput(iso: string) {
  const date = new Date(iso);
  if (Number.isNaN(date.getTime())) return "";
  const pad = (value: number) => String(value).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function GiveawayManager({ guildId }: { guildId: string }) {
  const [rows, setRows] = useState<GiveawayRow[]>([]);
  const [view, setView] = useState<GiveawayView>("live");
  const [roles, setRoles] = useState<{ id: string; name: string }[]>([]);
  const [channels, setChannels] = useState<ChannelOption[]>([]);
  const [selected, setSelected] = useState<string | null>(null);
  const [prize, setPrize] = useState("");
  const [description, setDescription] = useState("");
  const [channelId, setChannelId] = useState("");
  const [duration, setDuration] = useState("60");
  const [customEnd, setCustomEnd] = useState("");
  const [winners, setWinners] = useState("1");
  const [requiredRole, setRequiredRole] = useState("");
  const [blockedRole, setBlockedRole] = useState("");
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const body = await api.getGiveaways(guildId);
    setRows(body?.giveaways ?? []);
  }, [guildId]);

  useEffect(() => {
    void load().catch(() => setRows([]));
    api.getRoles(guildId).then((body) => setRoles(Array.isArray(body) ? body : [])).catch(() => setRoles([]));
    api.getChannels(guildId).then((body) => setChannels(Array.isArray(body) ? body : [])).catch(() => setChannels([]));
  }, [guildId, load]);

  const visible = useMemo(() => filterGiveaways(rows, view), [rows, view]);
  const draft = rows.find((row) => row.id === selected) ?? null;
  const channelName = (id: string | null) => {
    const channel = channels.find((item) => item.id === id);
    return channel ? `#${channel.name}` : "No channel";
  };
  const roleName = (id: string | null) => roles.find((role) => role.id === id)?.name || "None";
  const endsAt = duration === "custom" ? (customEnd ? new Date(customEnd).toISOString() : "") : new Date(Date.now() + Number(duration) * 60000).toISOString();

  async function create() {
    if (!prize.trim() || !channelId || !endsAt) {
      toast.error("Prize, channel, and end time are required");
      return;
    }
    setBusy(true);
    try {
      await api.createGiveaway(guildId, {
        prize: prize.trim(),
        description,
        channel_id: channelId,
        ends_at: endsAt,
        winner_count: Number(winners) || 1,
        required_role_id: requiredRole || null,
        blocked_role_id: blockedRole || null,
      });
      setPrize("");
      setDescription("");
      await load();
      setView("live");
      toast.success("Giveaway published");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not create the giveaway");
    } finally {
      setBusy(false);
    }
  }

  async function save(row: GiveawayRow, patch: Record<string, unknown>) {
    setBusy(true);
    try {
      await api.updateGiveaway(guildId, row.id, patch);
      await load();
      toast.success("Giveaway updated");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not update the giveaway");
    } finally {
      setBusy(false);
    }
  }

  async function act(kind: "end" | "reroll" | "archive", row: GiveawayRow) {
    setBusy(true);
    try {
      if (kind === "end") await api.endGiveaway(guildId, row.id);
      if (kind === "reroll") await api.rerollGiveaway(guildId, row.id);
      if (kind === "archive") await api.archiveGiveaway(guildId, row.id);
      await load();
      toast.success(kind === "end" ? "Giveaway ended" : kind === "reroll" ? "Winner rerolled" : "Giveaway archived");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not update the giveaway");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <PageHeader title="Giveaways" description="Publish a giveaway, take entries, and draw winners from the people who entered." />
      <div className="grid grid-cols-1 items-start gap-4 xl:grid-cols-[minmax(0,1fr)_22rem]">
        <div className="space-y-3">
          <div className="flex gap-2">
            {(["scheduled", "live", "ended"] as GiveawayView[]).map((item) => (
              <Button key={item} type="button" variant={view === item ? "secondary" : "ghost"} onClick={() => setView(item)}>
                {item === "live" ? "Live" : item === "scheduled" ? "Scheduled" : "Ended"}
              </Button>
            ))}
          </div>
          {visible.length === 0 ? (
            <p className="border border-line-subtle px-3 py-4 text-small text-fg-3">No {view} giveaways.</p>
          ) : (
            <ul className="divide-y divide-line-subtle border border-line-subtle">
              {visible.map((row) => (
                <li key={row.id}>
                  <button type="button" className="grid w-full grid-cols-1 gap-1 px-3 py-2 text-start hover:bg-surface-1 md:grid-cols-[minmax(0,1.4fr)_8rem_5rem_8rem_5rem]" onClick={() => setSelected(row.id)}>
                    <span className="min-w-0">
                      <span className="block truncate text-small text-fg-1">{row.prize}</span>
                      <span className="block truncate text-caption text-fg-3">{channelName(row.channel_id)}</span>
                    </span>
                    <span className="text-caption text-fg-2">{row.entry_count} entries</span>
                    <span className="text-caption text-fg-2">{row.winner_count} {row.winner_count === 1 ? "winner" : "winners"}</span>
                    <span className="text-caption text-fg-3">{new Date(row.ends_at).toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" })}</span>
                    <StatusLabel status={statusOf(row.status)}>{statusText(row.status)}</StatusLabel>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {draft ? (
            <GiveawayDetail
              row={draft}
              channelName={channelName(draft.channel_id)}
              roleName={roleName}
              roles={roles}
              busy={busy}
              onSave={(patch) => void save(draft, patch)}
              onAct={(kind) => void act(kind, draft)}
            />
          ) : null}
        </div>
        <form className="space-y-3 border border-line bg-surface-1 p-3" onSubmit={(event) => { event.preventDefault(); void create(); }}>
          <p className="text-small text-fg-1">New giveaway</p>
          <Input value={prize} onChange={(event) => setPrize(event.target.value)} placeholder="Prize" />
          <Textarea value={description} onChange={(event) => setDescription(event.target.value)} placeholder="Description" rows={3} />
          <ChannelPicker channels={channels} value={channelId} onChange={setChannelId} />
          <Select value={duration} onValueChange={setDuration} options={DURATIONS} />
          {duration === "custom" ? <Input type="datetime-local" value={customEnd} onChange={(event) => setCustomEnd(event.target.value)} /> : null}
          <p className="text-caption text-fg-3">Number of winners</p>
          <Input value={winners} onChange={(event) => setWinners(event.target.value)} inputMode="numeric" aria-label="Number of winners" />
          <p className="text-caption text-fg-3">Required role, optional</p>
          <RolePicker roles={roles} value={requiredRole} onChange={setRequiredRole} />
          {requiredRole ? <Button type="button" variant="ghost" onClick={() => setRequiredRole("")}>Clear required role</Button> : null}
          <p className="text-caption text-fg-3">Blocked role, optional</p>
          <RolePicker roles={roles} value={blockedRole} onChange={setBlockedRole} />
          {blockedRole ? <Button type="button" variant="ghost" onClick={() => setBlockedRole("")}>Clear blocked role</Button> : null}
          <DiscordMessagePreview
            guildId={guildId}
            message={{ content: giveawayPreview({ prize, description, winnerCount: Number(winners) || 1, endsAt, host: "you" }), embeds: [], buttons: [] }}
            values={{}}
          />
          <Button type="submit" disabled={busy}>Publish</Button>
        </form>
      </div>
    </div>
  );
}

function GiveawayDetail({
  row,
  channelName,
  roleName,
  roles,
  busy,
  onSave,
  onAct,
}: {
  row: GiveawayRow;
  channelName: string;
  roleName: (id: string | null) => string;
  roles: { id: string; name: string }[];
  busy: boolean;
  onSave: (patch: Record<string, unknown>) => void;
  onAct: (kind: "end" | "reroll" | "archive") => void;
}) {
  const [prize, setPrize] = useState(row.prize);
  const [description, setDescription] = useState(row.description || "");
  const [ends, setEnds] = useState(localInput(row.ends_at));
  const [winnerCount, setWinnerCount] = useState(String(row.winner_count));
  const [requiredRole, setRequiredRole] = useState(row.required_role_id || "");
  const [blockedRole, setBlockedRole] = useState(row.blocked_role_id || "");
  const editable = row.status === "open" || row.status === "scheduled";

  useEffect(() => {
    setPrize(row.prize);
    setDescription(row.description || "");
    setEnds(localInput(row.ends_at));
    setWinnerCount(String(row.winner_count));
    setRequiredRole(row.required_role_id || "");
    setBlockedRole(row.blocked_role_id || "");
  }, [row]);

  return (
    <div className="space-y-3 border border-line bg-surface-1 p-3">
      <div className="flex items-center justify-between gap-2">
        <p className="text-small text-fg-1">{row.prize}</p>
        <StatusLabel status={statusOf(row.status)}>{statusText(row.status)}</StatusLabel>
      </div>
      <p className="text-caption text-fg-3">{channelName} · {row.entry_count} entries · Host {row.host_name || "Unknown host"}</p>
      {row.winners?.length ? <p className="text-caption text-fg-2">Winners {row.winners.map((winner) => winner.name).join(", ")}</p> : null}
      {editable ? (
        <>
          <Input value={prize} onChange={(event) => setPrize(event.target.value)} aria-label="Prize" />
          <Textarea value={description} onChange={(event) => setDescription(event.target.value)} rows={3} aria-label="Description" />
          <Input type="datetime-local" value={ends} onChange={(event) => setEnds(event.target.value)} aria-label="End time" />
          <Input value={winnerCount} onChange={(event) => setWinnerCount(event.target.value)} inputMode="numeric" aria-label="Winner count" />
          <p className="text-caption text-fg-3">Required role · {roleName(requiredRole || null)}</p>
          <RolePicker roles={roles} value={requiredRole} onChange={setRequiredRole} />
          <p className="text-caption text-fg-3">Blocked role · {roleName(blockedRole || null)}</p>
          <RolePicker roles={roles} value={blockedRole} onChange={setBlockedRole} />
          <Button
            type="button"
            disabled={busy}
            onClick={() =>
              onSave({
                prize,
                description,
                ends_at: ends ? new Date(ends).toISOString() : row.ends_at,
                winner_count: Number(winnerCount) || 1,
                required_role_id: requiredRole || null,
                blocked_role_id: blockedRole || null,
                clear_required_role: !requiredRole,
                clear_blocked_role: !blockedRole,
              })
            }
          >
            Save
          </Button>
        </>
      ) : (
        <p className="text-small text-fg-2">{row.description || "No description."}</p>
      )}
      <div className="flex flex-wrap gap-2">
        {row.status === "open" ? <Button type="button" variant="secondary" disabled={busy} onClick={() => onAct("end")}>End now</Button> : null}
        {row.status === "ended" ? <Button type="button" variant="secondary" disabled={busy} onClick={() => onAct("reroll")}>Reroll</Button> : null}
        {row.status !== "archived" ? <Button type="button" variant="danger-secondary" disabled={busy} onClick={() => onAct("archive")}>Archive</Button> : null}
      </div>
    </div>
  );
}
