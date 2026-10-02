"use client";

import React, { useMemo, useState } from "react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";

const UNICODE = [
  ["smile", "😀"], ["grin", "😁"], ["joy", "😂"], ["smile", "😊"], ["heart eyes", "😍"], ["cool", "😎"],
  ["think", "🤔"], ["party", "🥳"], ["check", "✅"], ["cross", "❌"], ["warning", "⚠️"], ["fire", "🔥"],
  ["star", "⭐"], ["sparkle", "✨"], ["heart", "❤️"], ["purple", "💜"], ["thumb", "👍"], ["wave", "👋"],
  ["eyes", "👀"], ["pin", "📌"], ["book", "📖"], ["shield", "🛡️"], ["bell", "🔔"], ["link", "🔗"],
  ["red", "🔴"], ["blue", "🔵"], ["green", "🟢"],
];

export type GuildEmoji = { id: string; name: string; url: string; animated: boolean };

export function emojiToken(emoji: GuildEmoji): string {
  return `<${emoji.animated ? "a" : ""}:${emoji.name}:${emoji.id}>`;
}

export function EmojiPicker({
  value,
  emojis,
  onChange,
}: {
  value: string;
  emojis: GuildEmoji[];
  onChange: (emoji: string) => void;
}) {
  const [query, setQuery] = useState("");
  const needle = query.trim().toLowerCase();
  const custom = useMemo(
    () => emojis.filter((emoji) => !needle || emoji.name.toLowerCase().includes(needle)),
    [emojis, needle],
  );
  const unicode = UNICODE.filter(([name]) => !needle || name.includes(needle));
  const selected = emojis.find((emoji) => emojiToken(emoji) === value);
  const missing = value.startsWith("<") && !selected;

  return (
    <Popover>
      <PopoverTrigger asChild>
        <button type="button" className="flex h-8 min-w-8 items-center justify-center rounded-sm border border-line px-2 text-body" aria-label="Choose emoji">
          {selected ? (
            // eslint-disable-next-line @next/next/no-img-element
            <img src={selected.url} alt={selected.name} className="size-5" />
          ) : missing ? <span className="text-caption text-fg-3">Missing emoji</span> : (value || "😀")}
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-72 p-2">
        <input
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder="Search emoji"
          className="mb-2 h-8 w-full rounded-sm border border-line-input bg-surface-well px-2 text-caption"
        />
        {custom.length > 0 && (
          <div className="mb-2 grid grid-cols-6 gap-1">
            {custom.map((emoji) => (
              <button key={emoji.id} type="button" className="flex flex-col items-center rounded-sm p-1 hover:bg-bg-2" title={emoji.name} onClick={() => onChange(emojiToken(emoji))}>
                {/* eslint-disable-next-line @next/next/no-img-element */}
                <img src={emoji.url} alt={emoji.name} className="size-6" />
              </button>
            ))}
          </div>
        )}
        <div className="grid grid-cols-8 gap-0.5">
          {unicode.map(([name, glyph]) => (
            <button key={name + glyph} type="button" className="rounded-sm p-1 text-body hover:bg-bg-2" title={name} onClick={() => onChange(glyph)}>
              {glyph}
            </button>
          ))}
        </div>
        {value && (
          <button type="button" className="mt-2 text-caption text-fg-3" onClick={() => onChange("")}>
            Clear
          </button>
        )}
      </PopoverContent>
    </Popover>
  );
}
