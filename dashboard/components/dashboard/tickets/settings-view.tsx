"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/dashboard/page-header";
import { TicketsNav } from "@/components/dashboard/tickets/tickets-nav";
import { ChannelPicker, type ChannelOption } from "@/components/discord/channel-picker";
import { MemberPicker, type MemberChoice } from "@/components/discord/member-picker";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

function explain(err: unknown) {
  return err instanceof Error ? err.message : "Settings did not save.";
}

export function SettingsView({
  guildId,
  settings,
  channels,
  blocked,
}: {
  guildId: string;
  settings: Record<string, any>;
  channels: ChannelOption[];
  blocked: Array<Record<string, any>>;
}) {
  const router = useRouter();
  const [cooldown, setCooldown] = useState(Number(settings.cooldown_seconds ?? 60));
  const [maxOpen, setMaxOpen] = useState(Number(settings.max_open ?? 1));
  const [hours, setHours] = useState(settings.auto_close_hours ?? "");
  const [grace, setGrace] = useState(Number(settings.grace_minutes ?? 60));
  const [pattern, setPattern] = useState(String(settings.name_format || "ticket-{number}-{username}"));
  const [transcriptChannel, setTranscriptChannel] = useState(String(settings.transcript_channel_id || ""));
  const [reason, setReason] = useState("");
  const [member, setMember] = useState<MemberChoice | null>(null);
  const [query, setQuery] = useState("");
  const [tags, setTags] = useState<Array<{ id: string; name: string }>>([]);
  const [tagName, setTagName] = useState("");
  const [replies, setReplies] = useState<Array<{ id: string; name: string; content: string }>>([]);
  const [replyName, setReplyName] = useState("");
  const [replyBody, setReplyBody] = useState("");

  async function loadAdvanced() {
    const [tagBody, replyBodyResult] = await Promise.all([api.getTicketTags(guildId), api.getTicketReplies(guildId)]);
    setTags(tagBody.tags || []);
    setReplies(replyBodyResult.replies || []);
  }

  useEffect(() => {
    void Promise.all([api.getTicketTags(guildId), api.getTicketReplies(guildId)]).then(([tagBody, replyBodyResult]) => {
      setTags(tagBody.tags || []);
      setReplies(replyBodyResult.replies || []);
    }).catch(() => undefined);
  }, [guildId]);

  async function save() {
    try {
      await api.updateTicketLimits(guildId, {
        cooldown_seconds: cooldown,
        max_open: maxOpen,
        auto_close_hours: hours === "" ? 0 : Number(hours),
        grace_minutes: grace,
        transcript_channel_id: transcriptChannel || null,
        name_format: pattern,
      });
      toast.success("Settings saved");
      router.refresh();
    } catch (err) {
      toast.error(explain(err));
    }
  }

  async function block() {
    if (!member) return;
    try {
      await api.blacklistTicketUser(guildId, { user_id: member.id, reason, display_name: member.display_name, avatar: member.avatar });
      toast.success("Member blocked");
      setMember(null);
      setReason("");
      router.refresh();
    } catch (err) {
      toast.error(explain(err));
    }
  }

  const shown = blocked.filter((entry) => {
    const needle = query.trim().toLowerCase();
    if (!needle) return true;
    return `${entry.display_name} ${entry.reason}`.toLowerCase().includes(needle);
  });

  return (
    <div className="grid min-w-0 gap-4 xl:grid-cols-2">
      <div className="min-w-0 xl:col-span-2">
        <TicketsNav guildId={guildId} />
        <PageHeader title="Settings" description="Limits apply before a ticket channel is created." />
      </div>
      <section className="min-w-0 space-y-3 border border-line-subtle p-3">
        <label className="block text-small text-fg-2">Cooldown
          <Input type="number" value={cooldown} aria-label="Cooldown seconds" onChange={(event) => setCooldown(Number(event.target.value))} />
          <span className="text-caption text-fg-3">Seconds a member waits before opening another ticket. 0 disables it.</span>
        </label>
        <div className="flex flex-wrap gap-1">
          {[0, 30, 60, 300].map((value) => <Button key={value} type="button" size="sm" variant={cooldown === value ? "secondary" : "ghost"} onClick={() => setCooldown(value)}>{value === 0 ? "Off" : value < 60 ? `${value}s` : `${value / 60}m`}</Button>)}
        </div>
        <label className="block text-small text-fg-2">Max open tickets
          <Input type="number" min={1} max={10} value={maxOpen} aria-label="Max open tickets" onChange={(event) => setMaxOpen(Number(event.target.value))} />
          <span className="text-caption text-fg-3">How many open tickets one member may have in this server.</span>
        </label>
        <label className="block text-small text-fg-2">Auto-close after hours
          <Input value={hours} aria-label="Auto-close hours" placeholder="Off" onChange={(event) => setHours(event.target.value)} />
          <span className="text-caption text-fg-3">Leave empty to keep tickets open until staff close them.</span>
        </label>
        <div className="flex flex-wrap gap-1">
          {["", "12", "24", "48", "72"].map((value) => <Button key={value || "off"} type="button" size="sm" variant={String(hours) === value ? "secondary" : "ghost"} onClick={() => setHours(value)}>{value ? `${value}h` : "Off"}</Button>)}
        </div>
        <label className="block text-small text-fg-2">Warning grace, minutes
          <Input type="number" value={grace} aria-label="Grace minutes" onChange={(event) => setGrace(Number(event.target.value))} />
          <span className="text-caption text-fg-3">After the warning, the ticket closes if nobody replies.</span>
        </label>
        <label className="block text-small text-fg-2">Default channel name
          <Input value={pattern} aria-label="Channel name pattern" onChange={(event) => setPattern(event.target.value)} />
          <span className="text-caption text-fg-3">Used as the starting pattern for teams. {"{number}"} and {"{username}"} are filled in when the channel is created.</span>
        </label>
        <div>
          <p className="text-small text-fg-2">Transcript channel</p>
          <ChannelPicker channels={channels} value={transcriptChannel} onChange={setTranscriptChannel} />
          <p className="text-caption text-fg-3">Closed transcripts are posted here. The copy in CLS OS is kept either way.</p>
        </div>
        <Button type="button" onClick={() => void save()}>Save settings</Button>
      </section>
      <section className="min-w-0 space-y-3 border border-line-subtle p-3">
        <h2 className="text-small text-fg-1">Blacklist</h2>
        <p className="text-caption text-fg-3">Blocked members get a refusal instead of a ticket channel.</p>
        <MemberPicker guildId={guildId} onSelect={setMember} />
        {member && <p className="text-small text-fg-1">Blocking {member.display_name}</p>}
        <Input value={reason} onChange={(event) => setReason(event.target.value)} placeholder="Reason" aria-label="Block reason" />
        <Button type="button" disabled={!member} onClick={() => void block()}>Block member</Button>
        <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search blacklist" aria-label="Search blacklist" />
        {shown.length === 0 ? <p className="text-small text-fg-3">No one is blocked.</p> : (
          <ul className="divide-y divide-line-subtle border border-line-subtle">
            {shown.map((entry) => (
              <li key={entry.user_id} className="flex items-center justify-between gap-2 px-2 py-2">
                <div className="flex min-w-0 items-center gap-2">
                  {entry.avatar ? <img src={entry.avatar} alt="" className="size-6 rounded-full" /> : <span className="size-6 rounded-full bg-surface-2" />}
                  <div className="min-w-0">
                    <p className="truncate text-small text-fg-1">{entry.display_name || "Member"}</p>
                    <p className="truncate text-caption text-fg-3">{entry.reason || "No reason"} · {entry.created_at ? new Date(entry.created_at).toLocaleString() : ""}{entry.actor_name ? ` · ${entry.actor_name}` : ""}</p>
                  </div>
                </div>
                <Button type="button" size="sm" variant="ghost" onClick={() => void api.unblacklistTicketUser(guildId, entry.user_id).then(() => router.refresh())}>Unblock</Button>
              </li>
            ))}
          </ul>
        )}
      </section>
      <section className="min-w-0 space-y-3 border border-line-subtle p-3 lg:col-span-2">
        <h2 className="text-small text-fg-1">Tags</h2>
        <div className="flex gap-2">
          <Input value={tagName} aria-label="Tag name" placeholder="Billing" onChange={(event) => setTagName(event.target.value)} />
          <Button type="button" onClick={() => void api.createTicketTag(guildId, { name: tagName, position: tags.length }).then(() => { setTagName(""); return loadAdvanced(); }).catch((err) => toast.error(explain(err)))}>Add tag</Button>
        </div>
        {tags.map((tag, index) => (
          <div key={tag.id} className="flex flex-wrap items-center gap-2">
            <Input defaultValue={tag.name} aria-label={`Rename ${tag.name}`} onBlur={(event) => { if (event.target.value !== tag.name) void api.updateTicketTag(guildId, tag.id, { name: event.target.value, position: index }).then(loadAdvanced); }} />
            <Button type="button" size="sm" variant="ghost" disabled={index === 0} onClick={() => void api.updateTicketTag(guildId, tag.id, { name: tag.name, position: index - 1 }).then(loadAdvanced)}>Up</Button>
            <Button type="button" size="sm" variant="ghost" onClick={() => void api.deleteTicketTag(guildId, tag.id).then(loadAdvanced)}>Delete</Button>
          </div>
        ))}
        <h2 className="text-small text-fg-1">Saved replies</h2>
        <p className="text-caption text-fg-3">{"{number}"} and {"{opener}"} are filled in when the reply is sent. Choosing a reply does not send it.</p>
        <Input value={replyName} aria-label="Reply name" placeholder="Greeting" onChange={(event) => setReplyName(event.target.value)} />
        <Input value={replyBody} aria-label="Reply content" placeholder="Hello {opener}, this is ticket {number}." onChange={(event) => setReplyBody(event.target.value)} />
        <Button type="button" onClick={() => void api.createTicketReply(guildId, { name: replyName, content: replyBody }).then(() => { setReplyName(""); setReplyBody(""); return loadAdvanced(); }).catch((err) => toast.error(explain(err)))}>Save reply</Button>
        {replies.map((reply) => (
          <div key={reply.id} className="flex items-start justify-between gap-2 border border-line-subtle px-2 py-1">
            <p className="text-small text-fg-2"><span className="text-fg-1">{reply.name}. </span>{reply.content}</p>
            <Button type="button" size="sm" variant="ghost" onClick={() => void api.deleteTicketReply(guildId, reply.id).then(loadAdvanced)}>Delete</Button>
          </div>
        ))}
      </section>
    </div>
  );
}
