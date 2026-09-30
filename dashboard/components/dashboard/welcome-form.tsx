"use client";

import React, { useState } from "react";
import { Save, LayoutTemplate, RefreshCcw } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { WelcomeConfig, DiscordChannel } from "@/types/api";

interface WelcomeFormProps {
  initialConfig: WelcomeConfig;
  channels: DiscordChannel[];
  guildId: string;
}

export function WelcomeForm({ initialConfig, channels, guildId }: WelcomeFormProps) {
  const [config, setConfig] = useState<WelcomeConfig>(initialConfig);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.updateWelcome(guildId, config);
      toast.success("Welcome settings saved");
    } catch {
      toast.error("Failed to save welcome settings");
    } finally {
      setSaving(false);
    }
  };

  const channelOptions = channels.map((c) => ({
    value: String(c.id),
    label: `#${c.name}`,
  }));

  const typeOptions = [
    { value: "simple", label: "Simple text message" },
    { value: "embed", label: "Rich embed message" },
  ];

  return (
    <div className="grid grid-cols-1 gap-6 lg:grid-cols-[1fr_minmax(0,16rem)]">
      <div className="space-y-4 rounded-md border border-line bg-surface-1 p-4">
        <div className="space-y-2">
          <label className="text-body font-medium text-fg-1">Response type</label>
          <Select
            value={config.welcome_type || "simple"}
            onValueChange={(val) => setConfig({ ...config, welcome_type: val })}
            options={typeOptions}
          />
        </div>

        <div className="space-y-2">
          <label className="text-body font-medium text-fg-1">Welcome channel</label>
          <Select
            value={config.channel_id ? String(config.channel_id) : ""}
            onValueChange={(val) => setConfig({ ...config, channel_id: val ? val : null })}
            options={channelOptions}
            placeholder="Select a channel…"
          />
        </div>

        {config.welcome_type === "simple" && (
          <div className="space-y-2">
            <label className="text-body font-medium text-fg-1">Message content</label>
            <textarea
              value={config.welcome_message || ""}
              onChange={(e) => setConfig({ ...config, welcome_message: e.target.value })}
              placeholder="Welcome {user} to {server_name}!"
              className="min-h-[120px] w-full rounded-md border border-line bg-surface-2 p-3 text-body text-fg-1 focus:outline-none focus:ring-2 focus:ring-primary/40"
            />
          </div>
        )}

        {config.welcome_type === "embed" && (
          <div className="space-y-4 border-t border-line pt-4">
            <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
              <div className="space-y-2">
                <label className="text-body font-medium text-fg-1">Embed title</label>
                <input
                  type="text"
                  value={config.embed_data?.title || ""}
                  onChange={(e) => setConfig({ ...config, embed_data: { ...config.embed_data, title: e.target.value } })}
                  className="w-full rounded-md border border-line bg-surface-2 px-3 py-2 text-body text-fg-1"
                />
              </div>
              <div className="space-y-2">
                <label className="text-body font-medium text-fg-1">Embed color (hex)</label>
                <input
                  type="text"
                  value={config.embed_data?.color || ""}
                  onChange={(e) => setConfig({ ...config, embed_data: { ...config.embed_data, color: e.target.value } })}
                  className="w-full rounded-md border border-line bg-surface-2 px-3 py-2 text-body text-fg-1"
                  placeholder="#3498db"
                />
              </div>
            </div>
            <div className="space-y-2">
              <label className="text-body font-medium text-fg-1">Embed description</label>
              <textarea
                value={config.embed_data?.description || ""}
                onChange={(e) => setConfig({ ...config, embed_data: { ...config.embed_data, description: e.target.value } })}
                className="min-h-[100px] w-full rounded-md border border-line bg-surface-2 p-3 text-body text-fg-1"
              />
            </div>
          </div>
        )}

        <div className="flex justify-end pt-2">
          <Button onClick={() => void handleSave()} disabled={saving}>
            {saving ? <RefreshCcw className="size-4 animate-spin" aria-hidden="true" /> : <Save className="size-4" aria-hidden="true" />}
            Save changes
          </Button>
        </div>
      </div>

      <aside className="space-y-4">
        <div className="rounded-md border border-line bg-surface-1 p-4">
          <h3 className="text-body font-medium text-fg-1">Variables</h3>
          <ul className="mt-2 space-y-1 font-mono text-caption text-fg-2">
            <li>{"{user}"} — mention</li>
            <li>{"{user_name}"} — username</li>
            <li>{"{server_name}"} — server name</li>
            <li>{"{server_membercount}"} — member count</li>
            <li>{"{user_avatar}"} — avatar URL</li>
          </ul>
        </div>
        <Button
          type="button"
          variant="secondary"
          className="w-full"
          onClick={() =>
            setConfig({
              ...config,
              welcome_type: "embed",
              embed_data: {
                ...config.embed_data,
                title: "Welcome to {server_name}!",
                description: "Hi {user}, we're glad you joined! You are member #{server_membercount}.",
                color: "2f3136",
                thumbnail: "{user_avatar}",
              },
            })
          }
        >
          <LayoutTemplate className="size-4" aria-hidden="true" />
          Apply default template
        </Button>
      </aside>
    </div>
  );
}
