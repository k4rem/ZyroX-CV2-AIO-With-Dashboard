"use client";

import React, { useEffect, useState } from "react";
import { HexColorPicker } from "react-colorful";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { cn } from "@/lib/utils";

const PRESETS = ["#9474ff", "#5865f2", "#57f287", "#fee75c", "#ed4245", "#eb459e", "#ffffff", "#1e1f22"];
const STORAGE_KEY = "cls-message-colors";

function recentColors(): string[] {
  if (typeof window === "undefined") return [];
  try {
    const parsed = JSON.parse(window.localStorage.getItem(STORAGE_KEY) || "[]");
    return Array.isArray(parsed) ? parsed.filter((item) => typeof item === "string").slice(0, 8) : [];
  } catch {
    return [];
  }
}

export function ColorPicker({ value, onChange }: { value: string; onChange: (hex: string) => void }) {
  const [recent, setRecent] = useState<string[]>([]);
  const hex = /^#[0-9a-fA-F]{6}$/.test(value) ? value : "#9474ff";

  useEffect(() => setRecent(recentColors()), []);

  function remember(next: string) {
    const colors = [next, ...recent.filter((item) => item !== next)].slice(0, 8);
    setRecent(colors);
    window.localStorage.setItem(STORAGE_KEY, JSON.stringify(colors));
    onChange(next);
  }

  return (
    <div className="flex items-center gap-2">
      <Popover>
        <PopoverTrigger asChild>
          <button
            type="button"
            className="size-8 shrink-0 rounded-sm border border-line-strong"
            style={{ background: hex }}
            aria-label="Choose color"
          />
        </PopoverTrigger>
        <PopoverContent className="w-[232px] p-3">
          <HexColorPicker color={hex} onChange={(next) => onChange(next.toLowerCase())} />
          <div className="mt-3 flex flex-wrap gap-1.5">
            {PRESETS.map((preset) => (
              <button
                key={preset}
                type="button"
                className={cn("size-5 rounded-sm border border-line", preset === hex && "ring-1 ring-brand-400")}
                style={{ background: preset }}
                aria-label={preset}
                onClick={() => remember(preset)}
              />
            ))}
          </div>
          {recent.length > 0 && (
            <div className="mt-2 flex flex-wrap gap-1.5">
              {recent.map((preset) => (
                <button key={preset} type="button" className="size-5 rounded-sm border border-line" style={{ background: preset }} aria-label={`Recent ${preset}`} onClick={() => onChange(preset)} />
              ))}
            </div>
          )}
        </PopoverContent>
      </Popover>
      <input
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onBlur={() => {
          if (/^#[0-9a-fA-F]{6}$/.test(value)) remember(value.toLowerCase());
        }}
        spellCheck={false}
        aria-label="Hex color"
        className="h-8 w-[92px] rounded-sm border border-line-input bg-surface-well px-2 font-mono text-caption text-fg-1"
      />
    </div>
  );
}
