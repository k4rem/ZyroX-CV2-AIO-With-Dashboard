"use client";

import { useEffect, useId, useMemo, useState } from "react";
import { Check, ChevronDown, Folder, Hash, Megaphone, Mic, Volume2, type LucideIcon } from "lucide-react";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { nextComboboxIndex } from "@/lib/modulePayloads";
import { cn } from "@/lib/utils";

export interface ComboboxOption {
  value: string;
  label: string;
  meta?: string;
  swatch?: string | null;
  glyph?: "text" | "voice" | "category" | "announce" | "stage";
}

const GLYPH: Record<NonNullable<ComboboxOption["glyph"]>, LucideIcon> = {
  text: Hash,
  voice: Volume2,
  category: Folder,
  announce: Megaphone,
  stage: Mic,
};

function Glyph({ glyph }: { glyph?: ComboboxOption["glyph"] }) {
  if (!glyph) return null;
  const Icon = GLYPH[glyph];
  return <Icon className="size-3.5 shrink-0 text-fg-3" strokeWidth={1.75} aria-hidden="true" />;
}

function Swatch({ color }: { color?: string | null }) {
  if (!color) {
    return <span aria-hidden="true" className="size-2.5 shrink-0 rounded-full border border-fg-3" />;
  }
  return <span aria-hidden="true" className="size-2.5 shrink-0 rounded-full" style={{ backgroundColor: color }} />;
}

export function Combobox({
  id,
  value,
  onValueChange,
  options,
  placeholder = "Select…",
  searchLabel = "Search",
}: {
  id?: string;
  value: string | null;
  onValueChange: (value: string | null) => void;
  options: ComboboxOption[];
  placeholder?: string;
  searchLabel?: string;
}) {
  const [open, setOpen] = useState(false);
  const [query, setQuery] = useState("");
  const [active, setActive] = useState(0);
  const listId = useId();
  const selected = options.find((option) => (option.value || null) === (value || null)) ?? null;
  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase();
    if (!q) return options;
    return options.filter(
      (option) => option.label.toLowerCase().includes(q) || option.value === query.trim() || option.meta?.toLowerCase().includes(q),
    );
  }, [options, query]);

  useEffect(() => {
    setActive(0);
  }, [query, open]);

  const choose = (next: string) => {
    onValueChange(next === "" ? null : next);
    setOpen(false);
    setQuery("");
  };

  return (
    <Popover open={open} onOpenChange={setOpen}>
      <PopoverTrigger asChild>
        <button
          id={id}
          type="button"
          aria-haspopup="listbox"
          aria-expanded={open}
          className="flex h-8 w-full items-center gap-2 rounded-sm border border-line-input bg-surface-well px-2 text-start text-body text-fg-1 hover:border-fg-3 focus-visible:border-brand-400 focus-visible:outline-brand-400"
        >
          {selected?.swatch !== undefined ? <Swatch color={selected.swatch} /> : <Glyph glyph={selected?.glyph} />}
          <span className={cn("min-w-0 flex-1 truncate", !selected && "text-fg-3")}>{selected?.label ?? placeholder}</span>
          <ChevronDown className="size-3.5 shrink-0 text-fg-3" aria-hidden="true" />
        </button>
      </PopoverTrigger>
      <PopoverContent className="w-[var(--radix-popover-trigger-width)] p-0">
        <div className="border-b border-line-subtle p-2">
          <input
            aria-label={searchLabel}
            aria-controls={listId}
            aria-activedescendant={filtered[active] ? `${listId}-${active}` : undefined}
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search or paste an ID"
            className="h-8 w-full rounded-sm border border-line-input bg-surface-well px-2 text-body text-fg-1 outline-none focus-visible:border-brand-400"
            onKeyDown={(event) => {
              const pasted = options.find((option) => option.value === query.trim());
              if (event.key === "Enter" && pasted && active < 0) {
                event.preventDefault();
                choose(pasted.value);
                return;
              }
              const next = nextComboboxIndex(active, filtered.length, event.key);
              if (next === "close") {
                event.preventDefault();
                setOpen(false);
                return;
              }
              if (next === "select") {
                event.preventDefault();
                const exact = options.find((option) => option.value === query.trim());
                choose((exact ?? filtered[active]).value);
                return;
              }
              if (typeof next === "number") {
                event.preventDefault();
                setActive(next);
              }
            }}
          />
        </div>
        <ul id={listId} role="listbox" className="max-h-64 overflow-y-auto p-1">
          {filtered.length === 0 ? (
            <li className="px-2 py-2 text-small text-fg-3">No matches</li>
          ) : (
            filtered.map((option, index) => {
              const current = (option.value || null) === (value || null);
              return (
                <li key={`${option.value}-${option.label}`} role="presentation">
                  <button
                    id={`${listId}-${index}`}
                    type="button"
                    role="option"
                    aria-selected={current}
                    className={cn(
                      "flex h-8 w-full items-center gap-2 rounded-sm px-2 text-start text-body text-fg-1",
                      index === active && "bg-surface-3",
                    )}
                    onMouseEnter={() => setActive(index)}
                    onClick={() => choose(option.value)}
                  >
                    {option.swatch !== undefined ? <Swatch color={option.swatch} /> : <Glyph glyph={option.glyph} />}
                    <span className="min-w-0 flex-1 truncate">{option.label}</span>
                    {option.meta ? <span className="shrink-0 font-mono text-caption text-fg-3">{option.meta}</span> : null}
                    {current ? <Check className="size-3.5 text-fg-2" aria-hidden="true" /> : null}
                  </button>
                </li>
              );
            })
          )}
        </ul>
      </PopoverContent>
    </Popover>
  );
}
