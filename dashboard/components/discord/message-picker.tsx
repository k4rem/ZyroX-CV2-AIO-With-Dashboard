"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Input } from "@/components/ui/input";

export type MessageChoice = { id: string; channel_id: string; excerpt: string; author?: string };

export function MessagePicker({
  guildId,
  channelId,
  value,
  onChange,
}: {
  guildId: string;
  channelId: string;
  value: string;
  onChange: (message: MessageChoice) => void;
}) {
  const [link, setLink] = useState("");
  const [messages, setMessages] = useState<MessageChoice[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    if (!channelId) {
      setMessages([]);
      return;
    }
    api.getRoleMenuMessages(guildId, channelId).then((body) => setMessages(body.messages || [])).catch(() => setMessages([]));
  }, [guildId, channelId]);

  async function applyLink() {
    setError("");
    try {
      const body = await api.getRoleMenuMessages(guildId, channelId, link.trim());
      const message = body.messages?.[0];
      if (!message) {
        setError("That message was not found in this server.");
        return;
      }
      onChange(message);
    } catch (err) {
      setError(err instanceof Error ? err.message : "That message was not found.");
    }
  }

  return (
    <div className="space-y-2">
      {messages.length === 0 ? <p className="text-caption text-fg-3">Recent messages appear after you choose a channel.</p> : (
        <ul className="max-h-48 divide-y divide-line-subtle overflow-y-auto border border-line-subtle">
          {messages.map((message) => (
            <li key={message.id}>
              <button type="button" className={`block w-full px-2 py-1.5 text-left text-small ${value === message.id ? "bg-surface-2 text-fg-1" : "text-fg-2 hover:bg-surface-1"}`} onClick={() => onChange(message)}>
                <span className="block truncate">{message.excerpt}</span>
                <span className="text-caption text-fg-3">{message.author || "Message"}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
      <div className="flex gap-2">
        <Input value={link} onChange={(event) => setLink(event.target.value)} placeholder="Or paste a message link" aria-label="Message link" />
        <button type="button" className="shrink-0 text-small text-accent" onClick={() => void applyLink()}>Use link</button>
      </div>
      {error && <p className="text-caption text-fg-2">{error}</p>}
    </div>
  );
}
