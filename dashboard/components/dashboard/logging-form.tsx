"use client";

import React, { useState } from "react";
import {
  MessageSquare,
  UserPlus,
  ShieldAlert,
  Mic,
  Settings,
  Hash,
} from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Switch } from "@/components/ui/switch";
import { Select } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { LoggingConfig, DiscordChannel } from "@/types/api";

const LOG_CATEGORIES = [
  { id: "message_events", name: "Message events", icon: MessageSquare, description: "Message deletes, edits, and bulk removals." },
  { id: "join_leave_events", name: "Join and leave", icon: UserPlus, description: "Members joining or leaving the server." },
  { id: "member_moderation", name: "Moderation", icon: ShieldAlert, description: "Kicks, bans, and timeouts." },
  { id: "voice_events", name: "Voice", icon: Mic, description: "Voice channel join, leave, and moves." },
  { id: "role_events", name: "Roles", icon: Settings, description: "Role and permission changes." },
  { id: "channel_events", name: "Channels", icon: Hash, description: "Channel create, delete, and updates." },
];

interface LoggingFormProps {
  initialConfig: LoggingConfig;
  channels: DiscordChannel[];
  guildId: string;
}

export function LoggingForm({ initialConfig, channels, guildId }: LoggingFormProps) {
  const [config, setConfig] = useState<LoggingConfig>(initialConfig);
  const [saving, setSaving] = useState(false);

  const handleToggle = async (categoryId: string, enabled: boolean) => {
    const prev = config;
    const newLogEnabled = { ...config.log_enabled, [categoryId]: enabled };
    setConfig({ ...config, log_enabled: newLogEnabled });

    try {
      await api.updateLogging(guildId, {
        log_enabled: { [categoryId]: enabled },
      });
      toast.success(`${enabled ? "Enabled" : "Disabled"} ${categoryId.replace(/_/g, " ")}`);
    } catch {
      setConfig(prev);
      toast.error("Failed to update logging setting.");
    }
  };

  const handleChannelChange = async (categoryId: string, channelId: string) => {
    const prev = config;
    const newLogChannels = { ...config.log_channels, [categoryId]: channelId };
    setConfig({ ...config, log_channels: newLogChannels });

    setSaving(true);
    try {
      await api.updateLogging(guildId, {
        log_channels: { [categoryId]: channelId },
      });
      toast.success("Log channel updated");
    } catch {
      setConfig(prev);
      toast.error("Failed to update log channel");
    } finally {
      setSaving(false);
    }
  };

  const channelOptions = channels.map((c) => ({
    value: c.id,
    label: `#${c.name}`,
  }));

  const routed = LOG_CATEGORIES.filter(
    (category) => config.log_enabled[category.id] && config.log_channels[category.id],
  ).length;

  return (
    <div className="space-y-4">
      <p className="text-caption text-fg-2">
        {routed} of {LOG_CATEGORIES.length} categories are on and have a destination. Ignored:{" "}
        {config.ignore_roles.length} roles, {config.ignore_channels.length} channels.
      </p>
      {LOG_CATEGORIES.map((cat) => (
        <div
          key={cat.id}
          className="rounded-md border border-line bg-surface-1 p-4"
        >
          <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
            <div className="flex min-w-0 items-start gap-3">
              <cat.icon className="mt-0.5 size-5 shrink-0 text-fg-3" aria-hidden="true" />
              <div>
                <h3 className="text-body font-medium text-fg-1">{cat.name}</h3>
                <p className="mt-0.5 text-caption text-fg-2">{cat.description}</p>
              </div>
            </div>
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:gap-4">
              <div className="min-w-[12rem]">
                <label className="mb-1 block text-caption text-fg-3">Destination channel</label>
                <Select
                  value={config.log_channels[cat.id] ?? ""}
                  onValueChange={(val) => void handleChannelChange(cat.id, val)}
                  options={channelOptions}
                  placeholder="Select channel"
                  disabled={saving}
                />
              </div>
              <div className="flex items-center gap-2">
                <span className={cn("text-caption", config.log_enabled[cat.id] ? "text-fg-2" : "text-fg-3")}>
                  {config.log_enabled[cat.id] ? "Enabled" : "Off"}
                </span>
                <Switch
                  checked={!!config.log_enabled[cat.id]}
                  onCheckedChange={(val) => void handleToggle(cat.id, val)}
                  aria-label={`Toggle ${cat.name}`}
                />
              </div>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
