"use client";

import React, { useEffect, useState } from "react";
import {
  Zap,
  Type,
  Link as LinkIcon,
  MessageSquare,
  UserMinus,
  RefreshCcw,
  Save,
} from "lucide-react";
import { toast } from "sonner";
import { ChannelPicker, RolePicker, type ChannelOption } from "@/components/discord/channel-picker";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Select } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { AutomodConfig } from "@/types/api";

const PUNISHMENT_OPTIONS = [
  { value: "delete", label: "Delete message" },
  { value: "warn", label: "Warn user" },
  { value: "mute", label: "Mute user" },
  { value: "kick", label: "Kick user" },
  { value: "ban", label: "Ban user" },
];

const RULES = [
  { id: "anti_spam", name: "Anti spam", desc: "Repetitive or rapid messages.", icon: Zap },
  { id: "anti_caps", name: "Anti caps", desc: "Excessive uppercase.", icon: Type },
  { id: "anti_links", name: "Anti links", desc: "Unauthorized external links.", icon: LinkIcon },
  { id: "anti_invites", name: "Anti invites", desc: "Discord invite links.", icon: MessageSquare },
  { id: "anti_mentions", name: "Anti mass mention", desc: "@everyone and mass mentions.", icon: UserMinus },
];

interface AutomodFormProps {
  initialConfig: AutomodConfig;
  guildId: string;
}

export function AutomodForm({ initialConfig, guildId }: AutomodFormProps) {
  const [config, setConfig] = useState<AutomodConfig>(initialConfig);
  const [saving, setSaving] = useState(false);
  const [channels, setChannels] = useState<ChannelOption[]>([]);
  const [roles, setRoles] = useState<{ id: string; name: string }[]>([]);

  useEffect(() => {
    api.getChannels(guildId).then((body) => setChannels(Array.isArray(body) ? body : [])).catch(() => setChannels([]));
    api.getRoles(guildId).then((body) => setRoles(Array.isArray(body) ? body : [])).catch(() => setRoles([]));
  }, [guildId]);

  const handleToggleMaster = () => {
    setConfig({ ...config, enabled: !config.enabled });
  };

  const handlePunishmentChange = (ruleId: string, value: string) => {
    setConfig({ ...config, punishments: { ...config.punishments, [ruleId]: value } });
  };

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.updateAutomod(guildId, {
        enabled: config.enabled,
        punishments: config.punishments,
        ignored_channels: config.ignored_channels,
        ignored_roles: config.ignored_roles,
        logging_channel: config.logging_channel,
      });
      toast.success("Automod settings saved");
    } catch {
      toast.error("Failed to save automod settings");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between rounded-md border border-line bg-surface-1 px-4 py-3">
        <div>
          <p className="text-body font-medium text-fg-1">Automod enabled</p>
          <p className="text-caption text-fg-2" dir="auto">Master switch for all rules below.</p>
        </div>
        <Switch checked={config.enabled} onCheckedChange={handleToggleMaster} aria-label="Automod enabled" />
      </div>

      {!config.enabled && (
        <p className="text-caption text-fg-2" dir="auto">Turn on the master control to change rule settings.</p>
      )}

      <div className="grid grid-cols-1 gap-3 border border-line bg-surface-1 p-3 md:grid-cols-3">
        <div className="space-y-2">
          <p className="text-caption text-fg-3">Log channel</p>
          <ChannelPicker channels={channels} value={config.logging_channel || ""} onChange={(id) => setConfig({ ...config, logging_channel: id })} />
          {config.logging_channel ? (
            <button type="button" className="text-caption text-fg-3" onClick={() => setConfig({ ...config, logging_channel: null })}>Clear log channel</button>
          ) : null}
        </div>
        <div className="space-y-2">
          <p className="text-caption text-fg-3">Ignored channels</p>
          <ChannelPicker
            channels={channels}
            value=""
            onChange={(id) => setConfig({ ...config, ignored_channels: config.ignored_channels.includes(id) ? config.ignored_channels : [...config.ignored_channels, id] })}
          />
          {config.ignored_channels.map((id) => (
            <button key={id} type="button" className="block text-caption text-fg-2" onClick={() => setConfig({ ...config, ignored_channels: config.ignored_channels.filter((item) => item !== id) })}>
              #{channels.find((channel) => channel.id === id)?.name || "Unknown channel"} · remove
            </button>
          ))}
        </div>
        <div className="space-y-2">
          <p className="text-caption text-fg-3">Ignored roles</p>
          <RolePicker
            roles={roles}
            value=""
            onChange={(id) => setConfig({ ...config, ignored_roles: config.ignored_roles.includes(id) ? config.ignored_roles : [...config.ignored_roles, id] })}
          />
          {config.ignored_roles.map((id) => (
            <button key={id} type="button" className="block text-caption text-fg-2" onClick={() => setConfig({ ...config, ignored_roles: config.ignored_roles.filter((item) => item !== id) })}>
              {roles.find((role) => role.id === id)?.name || "Unknown role"} · remove
            </button>
          ))}
        </div>
      </div>

      <div className="space-y-3">
        {RULES.map((rule) => {
          const ruleOn = config.punishments?.[rule.id] !== undefined;
          const isEnabled = config.enabled && ruleOn;
          return (
            <div
              key={rule.id}
              className={cn(
                "rounded-md border border-line bg-surface-1 p-4",
                !config.enabled && "opacity-90",
              )}
            >
              <div className="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
                <div className="flex items-start gap-3">
                  <rule.icon className={cn("size-5 shrink-0", isEnabled ? "text-brand" : "text-fg-3")} aria-hidden="true" />
                  <div>
                    <h3 className="text-body font-medium text-fg-1">{rule.name}</h3>
                    <p className="text-caption text-fg-2" dir="auto">{rule.desc}</p>
                  </div>
                </div>
                <div className="flex flex-wrap items-center gap-3">
                  {config.enabled && ruleOn && (
                    <Select
                      value={config.punishments[rule.id] || "delete"}
                      onValueChange={(val) => handlePunishmentChange(rule.id, val)}
                      options={PUNISHMENT_OPTIONS}
                      className="w-40"
                    />
                  )}
                  <Switch
                    disabled={!config.enabled}
                    checked={ruleOn}
                    onCheckedChange={() => {
                      const newPunishments = { ...config.punishments };
                      if (newPunishments[rule.id]) delete newPunishments[rule.id];
                      else newPunishments[rule.id] = "delete";
                      setConfig({ ...config, punishments: newPunishments });
                    }}
                    aria-label={`Toggle ${rule.name}`}
                  />
                </div>
              </div>
            </div>
          );
        })}
      </div>

      <div className="flex justify-end pt-2">
        <Button onClick={() => void handleSave()} disabled={saving}>
          {saving ? <RefreshCcw className="size-4 animate-spin" aria-hidden="true" /> : <Save className="size-4" aria-hidden="true" />}
          Save changes
        </Button>
      </div>
    </div>
  );
}
