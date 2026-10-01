"use client";

import React, { useState } from "react";
import { toast } from "sonner";
import { SettingsInstrument } from "@/components/settings/settings-instrument";
import { api } from "@/lib/api";
import { Select } from "@/components/ui/select";
import { StatusLabel } from "@/components/ui/status";
import { Switch } from "@/components/ui/switch";
import { LoggingConfig, DiscordChannel } from "@/types/api";

const LOG_CATEGORIES = [
  { id: "message_events", name: "Message events", description: "Deletes, edits, and bulk removals." },
  { id: "join_leave_events", name: "Join and leave", description: "Members joining or leaving." },
  { id: "member_moderation", name: "Moderation", description: "Kicks, bans, and timeouts." },
  { id: "voice_events", name: "Voice", description: "Voice join, leave, and moves." },
  { id: "role_events", name: "Roles", description: "Role and permission changes." },
  { id: "channel_events", name: "Channels", description: "Channel create, delete, and updates." },
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
    <SettingsInstrument
      wide
      summary={`${routed} of ${LOG_CATEGORIES.length} enabled categories routed. Ignored: ${config.ignore_roles.length} roles, ${config.ignore_channels.length} channels.`}
    >
      <div className="overflow-x-auto">
        <table className="w-full min-w-[40rem] border-collapse text-start">
          <thead>
            <tr className="border-b border-line text-caption text-fg-3">
              <th className="py-2 pe-3 text-start font-medium">Category</th>
              <th className="py-2 pe-3 text-start font-medium">Enabled</th>
              <th className="py-2 pe-3 text-start font-medium">Destination</th>
              <th className="py-2 text-start font-medium">Routing</th>
            </tr>
          </thead>
          <tbody>
            {LOG_CATEGORIES.map((cat) => {
              const enabled = !!config.log_enabled[cat.id];
              const destination = config.log_channels[cat.id] ?? "";
              const routedRow = enabled && Boolean(destination);
              const routeStatus = !enabled ? "disabled" : routedRow ? "healthy" : "warning";
              const routeLabel = !enabled ? "Off" : routedRow ? "Routed" : "Incomplete";
              return (
                <tr key={cat.id} className="border-b border-line-subtle">
                  <td className="py-2 pe-3 align-middle">
                    <p className="text-body text-fg-1">{cat.name}</p>
                    <p className="text-caption text-fg-3" dir="auto">
                      {cat.description}
                    </p>
                  </td>
                  <td className="py-2 pe-3 align-middle">
                    <Switch
                      checked={enabled}
                      onCheckedChange={(val) => void handleToggle(cat.id, val)}
                      aria-label={`${cat.name} enabled`}
                      disabled={saving}
                    />
                  </td>
                  <td className="w-56 py-2 pe-3 align-middle">
                    <Select
                      value={destination}
                      onValueChange={(val) => void handleChannelChange(cat.id, val)}
                      options={channelOptions}
                      placeholder="Select channel"
                      disabled={saving}
                    />
                  </td>
                  <td className="py-2 align-middle">
                    <StatusLabel status={routeStatus}>{routeLabel}</StatusLabel>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </SettingsInstrument>
  );
}
