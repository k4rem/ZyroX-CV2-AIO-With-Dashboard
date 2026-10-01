"use client";

import { useEffect, useRef, useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { FlowLane, type FlowNodeModel } from "@/components/settings/flow-lane";
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
import { StatusLabel } from "@/components/ui/status";
import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api";
import { buildJ2CUpdate, j2cDraftFromApi, type J2CDraft } from "@/lib/modulePayloads";
import type { DiscordChannel } from "@/types/api";

const CONTROLS = ["Limit", "Privacy", "Thread", "Untrust", "Invite", "Kick", "Region", "Unblock", "Claim", "Transfer", "Delete", "Block"];

function byType(channels: DiscordChannel[], types: string[]): ComboboxOption[] {
  return channels
    .filter((channel) => types.includes(channel.type))
    .map((channel) => ({
      value: channel.id,
      label: channel.name,
      glyph: channel.type === "2" || channel.type === "13" ? "voice" : channel.type === "4" ? "category" : channel.type === "5" ? "announce" : "text",
      meta: channel.type === "13" ? "Stage" : undefined,
    }));
}

export function J2CWorkspace({
  guildId,
  initialConfig,
  channels,
}: {
  guildId: string;
  initialConfig: Parameters<typeof j2cDraftFromApi>[0];
  channels: DiscordChannel[];
}) {
  const { draft, setDraft, dirty, reset, commit } = useDraft<J2CDraft>(j2cDraftFromApi(initialConfig));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [confirmOff, setConfirmOff] = useState(false);
  const [selected, setSelected] = useState<string | null>("join");
  const [controlsOpen, setControlsOpen] = useState(false);
  const [width, setWidth] = useState(0);
  const [draw, setDraw] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const wasArmed = useRef(draft.enabled && Boolean(draft.join_channel_id && draft.control_channel_id));

  useEffect(() => {
    const node = rootRef.current?.parentElement ?? rootRef.current;
    if (!node) return;
    const observer = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width));
    observer.observe(node);
    return () => observer.disconnect();
  }, []);

  const join = channels.find((channel) => channel.id === draft.join_channel_id);
  const control = channels.find((channel) => channel.id === draft.control_channel_id);
  const category = channels.find((channel) => channel.id === draft.category_id);
  const parent = join?.parent_id ? channels.find((channel) => channel.id === join.parent_id) : null;
  const complete = Boolean(draft.join_channel_id && draft.control_channel_id);
  const armed = draft.enabled && complete;
  const vertical = width < 768;

  const tone = (ready: boolean): FlowNodeModel["tone"] => {
    if (!draft.enabled) return "neutral";
    return ready ? "set" : "missing";
  };

  const nodes: FlowNodeModel[] = [
    {
      id: "join",
      kicker: "Join channel",
      title: join?.name ?? "Pick a voice channel",
      detail: "Members join this channel",
      tone: tone(Boolean(join)),
    },
    {
      id: "temporary",
      kicker: "Temporary voice",
      title: category?.name ?? parent?.name ?? "Automatic",
      detail: category ? "Created in this category" : "Same category as the join channel",
      tone: draft.enabled ? (join ? "set" : "missing") : "neutral",
    },
    {
      id: "control",
      kicker: "Control panel",
      title: control?.name ?? "Pick a text channel",
      detail: `${CONTROLS.length} controls`,
      tone: tone(Boolean(control)),
    },
    {
      id: "cleanup",
      kicker: "Cleanup",
      title: "Deleted when empty",
      detail: "Last member leaving removes it",
      tone: draft.enabled ? "set" : "neutral",
    },
  ];

  const focusRow = (id: string) => {
    setSelected(id);
    const row = id === "temporary" ? "category" : id === "cleanup" ? "cleanup" : id;
    document.getElementById(`j2c-${row}`)?.scrollIntoView({ block: "nearest" });
    if (id === "control") setControlsOpen(true);
  };

  const save = async () => {
    setSaving(true);
    setError(null);
    const payload = buildJ2CUpdate(draft);
    try {
      await api.updateJ2C(guildId, payload);
      const becameArmed = payload.enabled && Boolean(payload.join_channel_id && payload.control_channel_id) && !wasArmed.current;
      wasArmed.current = Boolean(payload.enabled && payload.join_channel_id && payload.control_channel_id);
      commit(draft);
      if (becameArmed) {
        setDraw(false);
        requestAnimationFrame(() => setDraw(true));
      }
      toast.success("Join to Create saved");
    } catch {
      setError("Could not save Join to Create.");
      toast.error("Could not save Join to Create");
    } finally {
      setSaving(false);
    }
  };

  const status = !draft.enabled ? "disabled" : complete ? "online" : "warning";
  const statusLabel = !draft.enabled ? "Off" : complete ? "Active" : "Incomplete";

  return (
    <div ref={rootRef} className="w-full min-w-0 max-w-[1200px]">
      <PageHeader title="Join to Create" description="A member joins one voice channel and gets their own. It is removed when they leave.">
        <StatusLabel status={status}>{statusLabel}</StatusLabel>
        <span className="inline-flex items-center gap-2 text-small text-fg-2">
          <span>Enabled</span>
          <Switch
            checked={draft.enabled}
            aria-label="Enable Join to Create"
            onCheckedChange={(checked) => {
              if (checked) setDraft({ ...draft, enabled: true });
              else setConfirmOff(true);
            }}
          />
        </span>
      </PageHeader>

      <FlowLane
        nodes={nodes}
        selected={selected}
        onSelect={focusRow}
        armed={armed}
        animate={draw}
        vertical={vertical}
        caption={draft.enabled ? undefined : "Off — members joining voice channels get nothing. Saved channels stay in place."}
        extra={
          controlsOpen ? (
            <div className="mt-3 border-t border-line-subtle pt-3">
              <p className="text-small text-fg-2" dir="auto">The control panel posts these buttons. They are not edited here.</p>
              <ul className="mt-2 flex flex-wrap gap-1">
                {CONTROLS.map((controlName) => (
                  <li key={controlName} className="border border-line px-1.5 py-0.5 font-mono text-caption text-fg-2">
                    {controlName}
                  </li>
                ))}
              </ul>
            </div>
          ) : null
        }
      />

      <SettingGroup
        id="j2c-settings"
        label="Settings"
        meta={`${[draft.join_channel_id, draft.control_channel_id].filter(Boolean).length} of 2 required`}
      >
        <SettingRow id="j2c-join" label="Join channel" description="Members join this voice channel to get their own." selected={selected === "join"} htmlFor="j2c-join-input">
          <Combobox
            id="j2c-join-input"
            value={draft.join_channel_id}
            onValueChange={(value) => setDraft({ ...draft, join_channel_id: value })}
            options={byType(channels, ["2", "13"])}
            placeholder="Select a voice channel"
            searchLabel="Search voice channels"
          />
        </SettingRow>
        <SettingRow id="j2c-control" label="Control channel" description="Text channel where owners manage their channel." selected={selected === "control"} htmlFor="j2c-control-input">
          <Combobox
            id="j2c-control-input"
            value={draft.control_channel_id}
            onValueChange={(value) => setDraft({ ...draft, control_channel_id: value })}
            options={byType(channels, ["0", "5"])}
            placeholder="Select a text channel"
            searchLabel="Search text channels"
          />
        </SettingRow>
        <SettingRow id="j2c-category" label="Category" description="Where new channels are created. Automatic uses the join channel's category." selected={selected === "temporary"} htmlFor="j2c-category-input">
          <Combobox
            id="j2c-category-input"
            value={draft.category_id}
            onValueChange={(value) => setDraft({ ...draft, category_id: value })}
            options={[{ value: "", label: "Automatic (same as join)", glyph: "category" }, ...byType(channels, ["4"])]}
            placeholder="Automatic (same as join)"
            searchLabel="Search categories"
          />
        </SettingRow>
      </SettingGroup>
      <p id="j2c-cleanup" className="mt-3 text-small text-fg-3">
        Cleanup is not a setting. The bot deletes a temporary channel when its last member leaves.
      </p>
      <div className="mt-2">
        <Button type="button" variant="ghost" onClick={() => setControlsOpen((open) => !open)}>
          {controlsOpen ? "Hide control panel buttons" : "Show control panel buttons"}
        </Button>
      </div>

      <SaveBar dirty={dirty} saving={saving} error={error} onSave={() => void save()} onDiscard={reset} />

      <Dialog open={confirmOff} onOpenChange={setConfirmOff}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Turn off Join to Create?</DialogTitle>
            <DialogDescription>
              Members will no longer get a temporary channel. The join channel, control channel, and category stay saved.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button type="button" variant="secondary" onClick={() => setConfirmOff(false)}>
              Keep on
            </Button>
            <Button
              type="button"
              onClick={() => {
                setDraft({ ...draft, enabled: false });
                setConfirmOff(false);
              }}
            >
              Turn off
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
