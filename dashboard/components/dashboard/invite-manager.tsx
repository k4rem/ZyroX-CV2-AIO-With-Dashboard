"use client";

import React, { useEffect, useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { ChannelPicker, type ChannelOption } from "@/components/discord/channel-picker";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { inviteTotal, uncreditedCount, type InviteMember, type InviteOverview } from "@/lib/invites";

type Join = { user_id: string; name: string; code: string | null; joined_at: string; left_at: string | null };

const EMPTY: InviteOverview = {
  members: [],
  uncredited: { ambiguous: 0, unknown: 0, no_inviter: 0 },
  log_channel_id: null,
};

export function InviteManager({ guildId }: { guildId: string }) {
  const [overview, setOverview] = useState<InviteOverview>(EMPTY);
  const [channels, setChannels] = useState<ChannelOption[]>([]);
  const [channelId, setChannelId] = useState("");
  const [selected, setSelected] = useState<string | null>(null);
  const [detail, setDetail] = useState<{ name: string; codes: { code: string; uses: number }[]; joins: Join[]; valid: number; left: number } | null>(null);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    api.getInvitesV2(guildId).then((body) => {
      setOverview(body ?? EMPTY);
      setChannelId(body?.log_channel_id || "");
    }).catch(() => setOverview(EMPTY));
    api.getChannels(guildId).then((body) => setChannels(Array.isArray(body) ? body : [])).catch(() => setChannels([]));
  }, [guildId]);

  async function open(member: InviteMember) {
    setSelected(member.user_id);
    try {
      const body = await api.getInviteMember(guildId, member.user_id);
      setDetail(body);
    } catch {
      toast.error("Could not load this member");
    }
  }

  async function save() {
    setSaving(true);
    try {
      await api.saveInviteSettings(guildId, { log_channel_id: channelId || null });
      toast.success("Invite log saved");
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not save the log channel");
    } finally {
      setSaving(false);
    }
  }

  const uncredited = uncreditedCount(overview);

  return (
    <div className="space-y-4">
      <PageHeader
        title="Invites"
        description="A join is confirmed only when exactly one invite's use count goes up. If several change, or Discord shows none, nobody is credited."
      />
      <div className="grid grid-cols-1 items-start gap-4 lg:grid-cols-[minmax(0,1fr)_20rem]">
        <div className="space-y-3">
          {overview.members.length === 0 ? (
            <p className="border border-line-subtle px-3 py-4 text-small text-fg-3">No confirmed invites yet.</p>
          ) : (
            <ul className="divide-y divide-line-subtle border border-line-subtle">
              {overview.members.map((row) => (
                <li key={row.user_id}>
                  <button type="button" className="grid w-full grid-cols-2 gap-1 px-3 py-2 text-start hover:bg-surface-1 md:grid-cols-4" onClick={() => void open(row)}>
                    <span className="text-small text-fg-1">{row.name}</span>
                    <span className="text-caption text-fg-2">{row.valid} here</span>
                    <span className="text-caption text-fg-3">{row.left} left</span>
                    <span className="text-caption text-fg-2">{inviteTotal(row)} confirmed</span>
                  </button>
                </li>
              ))}
            </ul>
          )}
          {uncredited > 0 ? (
            <p className="text-small text-fg-3">
              Not credited: {overview.uncredited.unknown} unknown, {overview.uncredited.ambiguous} ambiguous
              {overview.uncredited.no_inviter ? `, ${overview.uncredited.no_inviter} with no inviter` : ""}.
            </p>
          ) : null}
          {detail && selected ? (
            <div className="space-y-2 border border-line bg-surface-1 p-3">
              <p className="text-small text-fg-1">{detail.name}</p>
              <p className="text-caption text-fg-3">{detail.valid} still here · {detail.left} left</p>
              <p className="text-caption text-fg-2">Codes {detail.codes.length ? detail.codes.map((item) => item.code).join(", ") : "none stored"}</p>
              {detail.joins.length === 0 ? <p className="text-small text-fg-3">No confirmed joins on these codes.</p> : (
                <ul className="divide-y divide-line-subtle border border-line-subtle">
                  {detail.joins.map((join) => (
                    <li key={`${join.user_id}-${join.joined_at}`} className="flex items-center justify-between gap-2 px-3 py-2 text-small">
                      <span className="text-fg-1">{join.name}</span>
                      <span className="text-caption text-fg-3">{join.left_at ? "Left" : "Here"} · {join.code}</span>
                    </li>
                  ))}
                </ul>
              )}
            </div>
          ) : null}
        </div>
        <div className="space-y-3 border border-line bg-surface-1 p-3">
          <p className="text-small text-fg-1">Join log</p>
          <p className="text-caption text-fg-3">Posts the attribution we can actually prove. There are no invite rewards.</p>
          <ChannelPicker channels={channels} value={channelId} onChange={setChannelId} />
          {channelId ? <Button type="button" variant="ghost" onClick={() => setChannelId("")}>Clear channel</Button> : null}
          <Button type="button" disabled={saving} onClick={() => void save()}>Save</Button>
        </div>
      </div>
    </div>
  );
}
