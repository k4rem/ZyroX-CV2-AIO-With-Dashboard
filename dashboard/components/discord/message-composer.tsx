"use client";

import React from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { ColorPicker } from "@/components/discord/color-picker";
import { EmojiPicker, type GuildEmoji } from "@/components/discord/emoji-picker";
import { MediaField } from "@/components/discord/media-field";
import { DiscordMessagePreview } from "@/components/discord/message-preview";
import { VariableTextField } from "@/components/discord/variable-text-field";
import {
  LIMITS,
  emptyEmbed,
  embedChars,
  messageChars,
  moveItem,
  type ButtonDraft,
  type EmbedDraft,
  type MessageDraft,
  type MessageVariable,
} from "@/lib/messagePayload";
import { cn } from "@/lib/utils";

export type ComposerSelection = { kind: "content" } | { kind: "embed"; index: number } | { kind: "button"; index: number };

function patchEmbed(message: MessageDraft, index: number, embed: EmbedDraft): MessageDraft {
  const embeds = message.embeds.slice();
  embeds[index] = embed;
  return { ...message, embeds };
}

export function MessageComposer({
  guildId,
  message,
  onChange,
  emojis,
  values,
  variables,
  selection,
  onSelect,
  showPreview,
  previewDensity = "desktop",
}: {
  guildId: string;
  message: MessageDraft;
  onChange: (next: MessageDraft) => void;
  emojis: GuildEmoji[];
  values: Record<string, string>;
  variables?: MessageVariable[];
  selection: ComposerSelection;
  onSelect: (next: ComposerSelection) => void;
  showPreview: boolean;
  previewDensity?: "desktop" | "mobile";
}) {
  const embed = selection.kind === "embed" ? message.embeds[selection.index] : null;
  const button = selection.kind === "button" ? message.buttons[selection.index] : null;

  function updateEmbed(next: EmbedDraft) {
    if (selection.kind !== "embed") return;
    onChange(patchEmbed(message, selection.index, next));
  }

  function updateButton(next: ButtonDraft) {
    if (selection.kind !== "button") return;
    const buttons = message.buttons.slice();
    buttons[selection.index] = next;
    onChange({ ...message, buttons });
  }

  return (
    <div className={cn("grid min-h-0 gap-3", showPreview ? "lg:grid-cols-[220px_minmax(0,1fr)_340px]" : "lg:grid-cols-[220px_minmax(0,1fr)]")}>
      <aside className="space-y-1 rounded-md border border-line bg-surface-1 p-2">
        <StructureButton active={selection.kind === "content"} label="Message" meta={`${message.content.length}/${LIMITS.content}`} onClick={() => onSelect({ kind: "content" })} />
        {message.embeds.map((item, index) => (
          <div key={index} className="flex items-center gap-1">
            <StructureButton
              active={selection.kind === "embed" && selection.index === index}
              label={item.title.trim() || `Embed ${index + 1}`}
              meta={`${embedChars(item)}`}
              onClick={() => onSelect({ kind: "embed", index })}
            />
            <Reorder
              onUp={() => {
                onChange({ ...message, embeds: moveItem(message.embeds, index, -1) });
                onSelect({ kind: "embed", index: Math.max(0, index - 1) });
              }}
              onDown={() => {
                onChange({ ...message, embeds: moveItem(message.embeds, index, 1) });
                onSelect({ kind: "embed", index: Math.min(message.embeds.length - 1, index + 1) });
              }}
            />
          </div>
        ))}
        {message.buttons.map((item, index) => (
          <StructureButton
            key={index}
            active={selection.kind === "button" && selection.index === index}
            label={item.label || `Button ${index + 1}`}
            meta="Link"
            onClick={() => onSelect({ kind: "button", index })}
          />
        ))}
        <div className="flex gap-1 pt-1">
          <Button type="button" variant="ghost" size="sm" disabled={message.embeds.length >= LIMITS.embeds} onClick={() => {
            onChange({ ...message, embeds: [...message.embeds, emptyEmbed()] });
            onSelect({ kind: "embed", index: message.embeds.length });
          }}>
            Add embed
          </Button>
          <Button type="button" variant="ghost" size="sm" disabled={message.buttons.length >= LIMITS.buttons} onClick={() => {
            onChange({ ...message, buttons: [...message.buttons, { label: "Open", url: "https://", emoji: "" }] });
            onSelect({ kind: "button", index: message.buttons.length });
          }}>
            Add link
          </Button>
        </div>
        <p className={cn("px-1 text-caption text-fg-4", messageChars(message) > LIMITS.embedTotal && "text-red-400")}>
          Embeds {messageChars(message)}/{LIMITS.embedTotal}
        </p>
      </aside>
      <section className="min-w-0 space-y-3 rounded-md border border-line bg-surface-1 p-3">
        {selection.kind === "content" && (
          <VariableTextField label="Message content" value={message.content} max={LIMITS.content} multiline variables={variables} onChange={(content) => onChange({ ...message, content })} />
        )}
        {embed && selection.kind === "embed" && (
          <div className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h2 className="text-body font-medium text-fg-1">Embed {selection.index + 1}</h2>
              <div className="flex gap-1">
                <Button type="button" variant="ghost" size="sm" onClick={() => {
                  const embeds = message.embeds.slice();
                  embeds.splice(selection.index + 1, 0, structuredClone(embed));
                  onChange({ ...message, embeds });
                }}>Duplicate</Button>
                <Button type="button" variant="danger-secondary" size="sm" onClick={() => {
                  const embeds = message.embeds.filter((_, index) => index !== selection.index);
                  onChange({ ...message, embeds });
                  onSelect({ kind: "content" });
                }}>Delete</Button>
              </div>
            </div>
            <VariableTextField label="Title" value={embed.title} max={LIMITS.title} variables={variables} onChange={(title) => updateEmbed({ ...embed, title })} />
            <label className="block space-y-1 text-caption text-fg-3">
              Title URL
              <Input value={embed.url} placeholder="https://" onChange={(event) => updateEmbed({ ...embed, url: event.target.value })} />
            </label>
            <VariableTextField label="Description" value={embed.description} max={LIMITS.description} multiline variables={variables} onChange={(description) => updateEmbed({ ...embed, description })} />
            <label className="block space-y-1 text-caption text-fg-3">
              Color
              <ColorPicker value={embed.color} onChange={(color) => updateEmbed({ ...embed, color })} />
            </label>
            <VariableTextField label="Author" value={embed.author.name} max={LIMITS.author} variables={variables} onChange={(name) => updateEmbed({ ...embed, author: { ...embed.author, name } })} />
            <label className="block space-y-1 text-caption text-fg-3">
              Author URL
              <Input value={embed.author.url} placeholder="https://" onChange={(event) => updateEmbed({ ...embed, author: { ...embed.author, url: event.target.value } })} />
            </label>
            <MediaField guildId={guildId} label="Author icon" value={embed.author.icon} onChange={(icon) => updateEmbed({ ...embed, author: { ...embed.author, icon } })} />
            <MediaField guildId={guildId} label="Thumbnail" value={embed.thumbnail} onChange={(thumbnail) => updateEmbed({ ...embed, thumbnail })} />
            <MediaField guildId={guildId} label="Image" value={embed.image} onChange={(image) => updateEmbed({ ...embed, image })} />
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-caption text-fg-3">Fields {embed.fields.length}/{LIMITS.fields}</span>
                <Button type="button" variant="ghost" size="sm" disabled={embed.fields.length >= LIMITS.fields} onClick={() => updateEmbed({ ...embed, fields: [...embed.fields, { name: "", value: "", inline: false }] })}>
                  Add field
                </Button>
              </div>
              {embed.fields.map((field, index) => (
                <div key={index} className="space-y-1.5 rounded-sm border border-line p-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-caption text-fg-3">Field {index + 1}</span>
                    <div className="flex items-center gap-2">
                      <span className="text-caption text-fg-3">Inline</span>
                      <Switch checked={field.inline} onCheckedChange={(inline) => {
                        const fields = embed.fields.slice();
                        fields[index] = { ...field, inline };
                        updateEmbed({ ...embed, fields });
                      }} />
                      <Reorder
                        onUp={() => updateEmbed({ ...embed, fields: moveItem(embed.fields, index, -1) })}
                        onDown={() => updateEmbed({ ...embed, fields: moveItem(embed.fields, index, 1) })}
                      />
                      <button type="button" className="text-caption text-fg-3" onClick={() => updateEmbed({ ...embed, fields: embed.fields.filter((_, fieldIndex) => fieldIndex !== index) })}>Delete</button>
                    </div>
                  </div>
                  <VariableTextField label="Name" value={field.name} max={LIMITS.fieldName} variables={variables} onChange={(name) => {
                    const fields = embed.fields.slice();
                    fields[index] = { ...field, name };
                    updateEmbed({ ...embed, fields });
                  }} />
                  <VariableTextField label="Value" value={field.value} max={LIMITS.fieldValue} multiline variables={variables} onChange={(value) => {
                    const fields = embed.fields.slice();
                    fields[index] = { ...field, value };
                    updateEmbed({ ...embed, fields });
                  }} />
                </div>
              ))}
            </div>
            <VariableTextField label="Footer" value={embed.footer.text} max={LIMITS.footer} variables={variables} onChange={(text) => updateEmbed({ ...embed, footer: { ...embed.footer, text } })} />
            <MediaField guildId={guildId} label="Footer icon" value={embed.footer.icon} onChange={(icon) => updateEmbed({ ...embed, footer: { ...embed.footer, icon } })} />
            <label className="flex items-center justify-between text-caption text-fg-2">
              Timestamp
              <Switch checked={embed.timestamp} onCheckedChange={(timestamp) => updateEmbed({ ...embed, timestamp })} />
            </label>
          </div>
        )}
        {button && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h2 className="text-body font-medium text-fg-1">Link button</h2>
              <Button type="button" variant="danger-secondary" size="sm" onClick={() => {
                onChange({ ...message, buttons: message.buttons.filter((_, index) => index !== (selection.kind === "button" ? selection.index : -1)) });
                onSelect({ kind: "content" });
              }}>Delete</Button>
            </div>
            <label className="block space-y-1 text-caption text-fg-3">
              Label
              <Input value={button.label} maxLength={LIMITS.buttonLabel} onChange={(event) => updateButton({ ...button, label: event.target.value })} />
            </label>
            <label className="block space-y-1 text-caption text-fg-3">
              URL
              <Input value={button.url} placeholder="https://" onChange={(event) => updateButton({ ...button, url: event.target.value })} />
            </label>
            <div className="flex items-center gap-2">
              <EmojiPicker value={button.emoji} emojis={emojis} onChange={(emoji) => updateButton({ ...button, emoji })} />
              <span className="text-caption text-fg-3">Button emoji</span>
            </div>
          </div>
        )}
      </section>
      {showPreview && (
        <aside className={cn("hidden min-w-0 lg:sticky lg:top-3 lg:block lg:self-start", previewDensity === "mobile" && "max-w-[300px]")}>
          <p className="mb-1 text-caption text-fg-3">Preview</p>
          <DiscordMessagePreview guildId={guildId} message={message} values={values} />
        </aside>
      )}
    </div>
  );
}

function StructureButton({ active, label, meta, onClick }: { active: boolean; label: string; meta: string; onClick: () => void }) {
  return (
    <button type="button" onClick={onClick} className={cn("flex min-w-0 flex-1 items-center justify-between gap-2 rounded-sm px-2 py-1.5 text-start", active ? "bg-bg-2 text-fg-1" : "text-fg-2 hover:bg-bg-2")}>
      <span className="truncate text-caption">{label}</span>
      <span className="shrink-0 text-caption text-fg-4">{meta}</span>
    </button>
  );
}

function Reorder({ onUp, onDown }: { onUp: () => void; onDown: () => void }) {
  return (
    <span className="flex flex-col">
      <button type="button" className="text-[10px] leading-none text-fg-3" aria-label="Move up" onClick={onUp}>↑</button>
      <button type="button" className="text-[10px] leading-none text-fg-3" aria-label="Move down" onClick={onDown}>↓</button>
    </span>
  );
}
