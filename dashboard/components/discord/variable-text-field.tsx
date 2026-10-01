"use client";

import React, { useMemo, useRef, useState } from "react";
import { STANDALONE_VARIABLES, insertAt, variableQuery, type MessageVariable } from "@/lib/messagePayload";
import { cn } from "@/lib/utils";

export function VariableTextField({
  label,
  value,
  onChange,
  max,
  multiline,
  variables = STANDALONE_VARIABLES,
}: {
  label: string;
  value: string;
  onChange: (next: string) => void;
  max: number;
  multiline?: boolean;
  variables?: MessageVariable[];
}) {
  const ref = useRef<HTMLTextAreaElement | HTMLInputElement>(null);
  const [cursor, setCursor] = useState(value.length);
  const [forced, setForced] = useState(false);
  const active = variableQuery(value, cursor);
  const open = forced || Boolean(active);
  const matches = useMemo(() => {
    const query = (active?.query || "").toLowerCase();
    return variables.filter((item) => !query || item.id.includes(query) || item.label.toLowerCase().includes(query));
  }, [active?.query, variables]);

  function place(token: string) {
    const el = ref.current;
    const start = active?.start ?? el?.selectionStart ?? value.length;
    const end = el?.selectionEnd ?? start;
    const next = insertAt(value, start, active ? cursor : end, token);
    onChange(next.value);
    setForced(false);
    requestAnimationFrame(() => {
      el?.focus();
      el?.setSelectionRange(next.cursor, next.cursor);
      setCursor(next.cursor);
    });
  }

  const shared = {
    ref: ref as React.Ref<HTMLTextAreaElement & HTMLInputElement>,
    value,
    "aria-label": label,
    onSelect: (event: React.SyntheticEvent<HTMLInputElement | HTMLTextAreaElement>) => setCursor(event.currentTarget.selectionStart || 0),
    onChange: (event: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
      onChange(event.target.value);
      setCursor(event.target.selectionStart || 0);
      setForced(false);
    },
    className:
      "w-full rounded-sm border border-line-input bg-surface-well px-2.5 py-1.5 text-body text-fg-1 shadow-well focus-visible:border-brand-400 focus-visible:outline-none",
  };

  return (
    <label className="block space-y-1">
      <span className="flex items-center justify-between gap-2 text-caption text-fg-3">
        <span>{label}</span>
        <span className={cn(value.length > max && "text-red-400")}>
          {value.length}/{max}
        </span>
      </span>
      <div className="flex items-start gap-1">
        {multiline ? <textarea {...shared} rows={4} /> : <input {...shared} />}
        <button
          type="button"
          className="h-8 shrink-0 rounded-sm border border-line px-1.5 font-mono text-caption text-fg-2 hover:text-fg-1"
          aria-label={`Insert variable in ${label}`}
          onClick={() => setForced((openNow) => !openNow)}
        >
          {"{}"}
        </button>
      </div>
      {open && matches.length > 0 && (
        <ul className="max-h-40 overflow-auto rounded-sm border border-line bg-surface-1">
          {matches.map((item) => (
            <li key={item.id}>
              <button type="button" className="flex w-full flex-col px-2 py-1.5 text-start hover:bg-bg-2" onClick={() => place(`{${item.id}}`)}>
                <span className="font-mono text-caption text-fg-1">{`{${item.id}}`}</span>
                <span className="text-caption text-fg-3">
                  {item.description} · {item.example}
                </span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </label>
  );
}
