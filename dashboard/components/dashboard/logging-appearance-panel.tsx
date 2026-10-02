"use client";

import React from "react";
import { Input } from "@/components/ui/input";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

export type Appearance = {
  style: "compact" | "balanced" | "detailed";
  show_avatars: boolean;
  show_moderator: boolean;
  show_jump: boolean;
  show_timestamp: boolean;
  show_ids: boolean;
  footer_mode: "cls" | "custom" | "off";
  footer_text: string | null;
  colors: Record<string, string>;
  event_styles?: Record<string, { use_default?: boolean; color?: string; icon?: string; title?: string }>;
  ignore_scope?: "messages" | "all";
};

const FALLBACK: Record<string, string> = {
  message_events: "#4F6BED",
  join_leave_events: "#2F9E6B",
  member_moderation: "#C44B4B",
  voice_events: "#6B7280",
  role_events: "#C4A15A",
  channel_events: "#4F6BED",
  guild_events: "#6B7280",
  bot_actions: "#6B7280",
  automod: "#8B5CF6",
  security: "#C44B4B",
};

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

const SWATCHES = ["#4F6BED", "#2F9E6B", "#C44B4B", "#C4A15A", "#8B5CF6", "#6B7280", "#E8E4DC", "#111111"];

const SAMPLES = [
  { id: "message_edit", category: "message_events", title: "Message edited", sentence: "AERO edited a message in #general", change: "logging test 1 → logging test 2" },
  { id: "member_roles", category: "role_events", title: "Role added", sentence: "+EVO+ received R7 Extra", change: "+ R7 Extra" },
  { id: "role_update", category: "role_events", title: "Role updated", sentence: "@VIP was updated", change: "VIP → VIP Customer" },
  { id: "channel_update", category: "channel_events", title: "Channel updated", sentence: "#general permissions updated", change: "Send Messages: Allow → Deny" },
  { id: "automod.flood", category: "automod", title: "Message flood", sentence: "Spam detected", change: "9 messages in 4.1s" },
  { id: "security.incident_created", category: "security", title: "Incident created", sentence: "Role deletion", change: "Confidence recorded" },
];

export function LoggingAppearancePanel({
  appearance,
  onChange,
}: {
  appearance: Appearance;
  onChange: (patch: Partial<Appearance> & { colors?: Record<string, string> }) => void;
}) {
  const [sampleId, setSampleId] = React.useState("message_edit");
  const sample = SAMPLES.find((item) => item.id === sampleId) || SAMPLES[0];
  const eventStyle = appearance.event_styles?.[sample.id];
  const usingDefault = eventStyle?.use_default !== false;
  const color = (!usingDefault && eventStyle?.color) || appearance.colors[sample.category] || FALLBACK[sample.category] || FALLBACK.message_events;
  const style = appearance.style;
  return (
    <div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_24rem]">
      <div className="space-y-6">
        <section>
          <h2 className="text-small font-medium text-fg-1">Style</h2>
          <p className="mb-2 text-caption text-fg-3">How much a Discord log embed shows. Stored evidence stays the same.</p>
          <div className="flex flex-wrap gap-1">
            {(["compact", "balanced", "detailed"] as const).map((item) => (
              <button
                key={item}
                type="button"
                className={`px-2 py-1 text-small capitalize ${style === item ? "bg-bg-2 text-fg-1 ring-1 ring-brand-400" : "text-fg-2 ring-1 ring-line"}`}
                onClick={() => onChange({ style: item })}
              >
                {item}
              </button>
            ))}
          </div>
        </section>
        <section>
          <h2 className="mb-2 text-small font-medium text-fg-1">Display</h2>
          <ul className="divide-y divide-line-subtle border-y border-line-subtle">
            <Toggle label="Show avatars" checked={appearance.show_avatars} onChange={(show_avatars) => onChange({ show_avatars })} />
            <Toggle label="Show moderator" checked={appearance.show_moderator} onChange={(show_moderator) => onChange({ show_moderator })} />
            <Toggle label="Show jump button" checked={appearance.show_jump} onChange={(show_jump) => onChange({ show_jump })} />
            <Toggle label="Show timestamp" checked={appearance.show_timestamp} onChange={(show_timestamp) => onChange({ show_timestamp })} />
            <Toggle label="Show IDs in footer" checked={appearance.show_ids} onChange={(show_ids) => onChange({ show_ids })} />
          </ul>
        </section>
        <section>
          <h2 className="mb-2 text-small font-medium text-fg-1">Category colors</h2>
          <ul className="grid gap-2 sm:grid-cols-2">
            {Object.keys(FALLBACK).map((category) => (
              <li key={category} className="flex items-center justify-between gap-2">
                <span className="text-small text-fg-1">{LABELS[category]}</span>
                <ColorField
                  value={appearance.colors[category] || FALLBACK[category]}
                  onChange={(value) => onChange({ colors: { [category]: value } })}
                />
              </li>
            ))}
          </ul>
        </section>
        <section>
          <h2 className="mb-2 text-small font-medium text-fg-1">Event appearance</h2>
          <p className="mb-2 text-caption text-fg-3">Category color is the default. A per-event override can change color, icon, and title.</p>
          <div className="mb-2 flex flex-wrap gap-1">
            {SAMPLES.map((item) => (
              <button key={item.id} type="button" className={`px-2 py-1 text-small ${sample.id === item.id ? "bg-bg-2 text-fg-1 ring-1 ring-brand-400" : "text-fg-2 ring-1 ring-line"}`} onClick={() => setSampleId(item.id)}>
                {item.title}
              </button>
            ))}
          </div>
          <button
            type="button"
            className="mb-2 text-small text-fg-1"
            onClick={() => onChange({ event_styles: { [sample.id]: { ...(eventStyle || {}), use_default: !usingDefault } } })}
          >
            Use category default: {usingDefault ? "On" : "Off"}
          </button>
          {usingDefault ? null : (
            <div className="flex flex-wrap items-center gap-2">
              <ColorField value={eventStyle?.color || color} onChange={(value) => onChange({ event_styles: { [sample.id]: { ...(eventStyle || {}), use_default: false, color: value } } })} />
              <Input className="max-w-xs" value={eventStyle?.title || sample.title} aria-label="Event title" onChange={(event) => onChange({ event_styles: { [sample.id]: { ...(eventStyle || {}), use_default: false, title: event.target.value } } })} />
            </div>
          )}
        </section>
        <section>
          <h2 className="mb-2 text-small font-medium text-fg-1">Brand footer</h2>
          <div className="flex flex-wrap gap-1">
            {(["cls", "custom", "off"] as const).map((mode) => (
              <button
                key={mode}
                type="button"
                className={`px-2 py-1 text-small ${appearance.footer_mode === mode ? "bg-bg-2 text-fg-1 ring-1 ring-brand-400" : "text-fg-2 ring-1 ring-line"}`}
                onClick={() => onChange({ footer_mode: mode })}
              >
                {mode === "cls" ? "CLS" : mode === "custom" ? "Custom text" : "Off"}
              </button>
            ))}
          </div>
          {appearance.footer_mode === "custom" ? (
            <Input
              className="mt-2 max-w-xs"
              value={appearance.footer_text || ""}
              maxLength={80}
              aria-label="Custom footer"
              placeholder="Footer text"
              onChange={(event) => onChange({ footer_text: event.target.value })}
            />
          ) : null}
        </section>
      </div>
      <Preview appearance={appearance} color={color} title={usingDefault ? sample.title : eventStyle?.title || sample.title} sentence={sample.sentence} change={sample.change} />
    </div>
  );
}

function Toggle({ label, checked, onChange }: { label: string; checked: boolean; onChange: (value: boolean) => void }) {
  return (
    <li className="flex items-center justify-between gap-3 py-2">
      <span className="text-small text-fg-1">{label}</span>
      <button
        type="button"
        role="switch"
        aria-checked={checked}
        aria-label={label}
        className={`h-5 w-9 rounded-full ${checked ? "bg-brand-400" : "bg-bg-2 ring-1 ring-line"}`}
        onClick={() => onChange(!checked)}
      >
        <span className={`block size-4 rounded-full bg-fg-1 ${checked ? "translate-x-4" : "translate-x-0.5"}`} />
      </button>
    </li>
  );
}

function ColorField({ value, onChange }: { value: string; onChange: (value: string) => void }) {
  const [draft, setDraft] = React.useState(value);
  React.useEffect(() => setDraft(value), [value]);
  const commit = (next: string) => {
    setDraft(next);
    if (/^#[0-9a-fA-F]{6}$/.test(next)) onChange(next);
  };
  return (
    <Popover>
      <PopoverTrigger asChild>
        <button type="button" className="flex items-center gap-2 text-caption text-fg-2" aria-label={`Color ${value}`}>
          <span className="size-4 border border-line" style={{ background: value }} />
          {value}
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-56 p-3">
        <div className="mb-2 grid grid-cols-8 gap-1">
          {SWATCHES.map((swatch) => (
            <button key={swatch} type="button" aria-label={swatch} className="size-5 border border-line" style={{ background: swatch }} onClick={() => commit(swatch)} />
          ))}
        </div>
        <div className="flex items-center gap-2">
          <input type="color" aria-label="Pick color" value={/^#[0-9a-fA-F]{6}$/.test(draft) ? draft : value} onChange={(event) => commit(event.target.value)} />
          <Input value={draft} aria-label="Hex color" onChange={(event) => commit(event.target.value)} />
        </div>
      </PopoverContent>
    </Popover>
  );
}

function Preview({ appearance, color, title, sentence, change }: { appearance: Appearance; color: string; title: string; sentence: string; change: string }) {
  const brand = appearance.footer_mode === "off" ? "" : appearance.footer_mode === "custom" ? appearance.footer_text || "Custom" : "CLS";
  const footer = [brand, title, appearance.show_ids ? "User ID: 100" : ""].filter(Boolean).join(" • ");
  const detailed = appearance.style === "detailed";
  const compact = appearance.style === "compact";
  return (
    <aside className="border border-line-subtle p-4 lg:sticky lg:top-4">
      <p className="mb-2 text-caption text-fg-3">Preview · {title}</p>
      <div className="min-h-48 border border-line bg-bg-1 p-4" style={{ borderLeft: `3px solid ${color}` }}>
        <div className="mb-2 flex items-center gap-2">
          {appearance.show_avatars ? <span draggable={false} className="grid size-8 place-items-center rounded-full bg-bg-2 text-caption">A</span> : null}
          <span className="text-small text-fg-1">AERO</span>
        </div>
        <p className="text-small font-medium text-fg-1">{title}</p>
        <p className="mt-1 text-small text-fg-2">
          {sentence}
          {compact ? <span className="mt-1 block text-fg-1">{change}</span> : null}
        </p>
        {compact ? null : (
          <div className="mt-2 space-y-2">
            <div>
              <p className="text-caption text-fg-3">Change</p>
              <p className="text-small text-fg-1">{change}</p>
            </div>
            {detailed ? (
              <div>
                <p className="text-caption text-fg-3">Channel</p>
                <p className="text-small text-fg-1">#public-chat</p>
              </div>
            ) : null}
            {appearance.show_moderator && detailed ? (
              <div>
                <p className="text-caption text-fg-3">Moderator</p>
                <p className="text-small text-fg-1">CLS SYSTEM</p>
              </div>
            ) : null}
          </div>
        )}
        {appearance.show_jump ? <p className="mt-2 inline-block border border-line px-2 py-1 text-caption text-fg-1">View message</p> : null}
        <p className="mt-2 text-caption text-fg-3">
          {footer}
          {appearance.show_timestamp ? " · just now" : ""}
        </p>
      </div>
    </aside>
  );
}
