"use client";

import React, { useRef, useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { api, ApiError } from "@/lib/api";
import type { MediaRef } from "@/lib/messagePayload";

export function mediaSrc(guildId: string, ref: MediaRef): string {
  if (!ref?.value) return "";
  if (ref.kind === "media") return `/api/bot/guilds/${guildId}/media/${ref.value}`;
  return ref.value;
}

export function MediaField({
  guildId,
  label,
  value,
  onChange,
}: {
  guildId: string;
  label: string;
  value: MediaRef;
  onChange: (next: MediaRef) => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const [url, setUrl] = useState(value?.kind === "url" ? value.value : "");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const src = mediaSrc(guildId, value);

  async function upload(file: File) {
    setBusy(true);
    setError("");
    try {
      const body = new FormData();
      body.append("file", file);
      const saved = await api.uploadMessageMedia(guildId, body);
      onChange({ kind: "media", value: saved.key });
      setUrl("");
    } catch (err) {
      setError(err instanceof ApiError ? String(err.message) : "Upload failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-1.5">
      <div className="flex items-center justify-between gap-2">
        <span className="text-caption text-fg-3">{label}</span>
        {value && (
          <button type="button" className="text-caption text-fg-3 hover:text-fg-1" onClick={() => onChange(null)}>
            Remove
          </button>
        )}
      </div>
      {src && (
        // eslint-disable-next-line @next/next/no-img-element
        <img src={src} alt="" className="max-h-24 rounded-sm border border-line object-contain" />
      )}
      <div className="flex gap-1.5">
        <Button type="button" variant="secondary" size="sm" disabled={busy} onClick={() => input.current?.click()}>
          {value ? "Replace" : "Upload"}
        </Button>
        <Input
          value={url}
          placeholder="https://"
          onChange={(event) => setUrl(event.target.value)}
          onBlur={() => {
            const next = url.trim();
            if (!next) return;
            onChange({ kind: "url", value: next });
          }}
          aria-label={`${label} URL`}
        />
      </div>
      <input
        ref={input}
        type="file"
        accept="image/png,image/jpeg,image/gif,image/webp"
        className="hidden"
        onChange={(event) => {
          const file = event.target.files?.[0];
          if (file) void upload(file);
          event.target.value = "";
        }}
      />
      {error && <p className="text-caption text-red-400">{error}</p>}
    </div>
  );
}
