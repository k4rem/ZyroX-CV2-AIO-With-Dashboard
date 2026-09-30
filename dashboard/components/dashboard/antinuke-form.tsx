"use client";

import React, { useState } from "react";
import { ShieldAlert, User, RefreshCcw, Save, Trash2 } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { cn } from "@/lib/utils";
import { AntiNukeConfig } from "@/types/api";
import { normalizeSnowflakeInput } from "@/lib/snowflake";

interface AntiNukeFormProps {
  initialConfig: AntiNukeConfig;
  guildId: string;
}

export function AntiNukeForm({ initialConfig, guildId }: AntiNukeFormProps) {
  const [config, setConfig] = useState<AntiNukeConfig>(initialConfig);
  const [saving, setSaving] = useState(false);
  const [wlInput, setWlInput] = useState("");
  const [whitelistedUsers, setWhitelistedUsers] = useState<string[]>(initialConfig.whitelisted_users || []);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.updateAntiNuke(guildId, { status: config.status });
      toast.success("Antinuke settings saved");
    } catch {
      toast.error("Failed to save antinuke settings");
    } finally {
      setSaving(false);
    }
  };

  const handleAddWhitelist = async () => {
    const uid = normalizeSnowflakeInput(wlInput);
    if (!uid) {
      toast.error("Enter a valid user ID");
      return;
    }
    if (whitelistedUsers.includes(uid)) {
      toast.error("User is already whitelisted");
      return;
    }
    setSaving(true);
    try {
      await api.updateAntiNuke(guildId, { status: config.status, add_whitelist: uid });
      setWhitelistedUsers([...whitelistedUsers, uid]);
      setWlInput("");
      toast.success("User added to whitelist");
    } catch {
      toast.error("Failed to update whitelist");
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveWhitelist = async (userId: string) => {
    setSaving(true);
    try {
      await api.updateAntiNuke(guildId, { status: config.status, remove_whitelist: userId });
      setWhitelistedUsers(whitelistedUsers.filter((id) => id !== userId));
      toast.success("User removed from whitelist");
    } catch {
      toast.error("Failed to remove user");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between rounded-md border border-line bg-surface-1 px-4 py-3">
        <div>
          <p className="text-body font-medium text-fg-1">Antinuke enabled</p>
          <p className="text-caption text-fg-2">Protections against destructive admin actions when enabled.</p>
        </div>
        <Switch
          checked={config.status}
          onCheckedChange={(v) => setConfig({ ...config, status: v })}
          aria-label="Antinuke enabled"
        />
      </div>

      {!config.status && (
        <p className="text-caption text-fg-2">Turn on the master control to manage whitelist entries.</p>
      )}

      <section className={cn("rounded-md border border-line bg-surface-1 p-4", !config.status && "opacity-90")}>
        <h3 className="text-section-title text-fg-1">Whitelist</h3>
        <p className="mt-1 text-caption text-fg-2">Trusted user IDs exempt from antinuke triggers.</p>
        <div className="mt-3 flex flex-col gap-2 sm:flex-row">
          <Input
            value={wlInput}
            onChange={(e) => setWlInput(e.target.value)}
            placeholder="Discord user ID"
            dir="ltr"
            className="font-mono"
            disabled={!config.status}
            inputMode="numeric"
          />
          <Button type="button" variant="secondary" onClick={() => void handleAddWhitelist()} disabled={!config.status || saving}>
            Add
          </Button>
        </div>
        <ul className="mt-4 space-y-2">
          {whitelistedUsers.length === 0 ? (
            <li className="text-caption text-fg-3">No whitelisted users.</li>
          ) : (
            whitelistedUsers.map((userId) => (
              <li key={userId} className="flex items-center justify-between gap-2 rounded-md border border-line px-3 py-2">
                <span className="font-mono text-body text-fg-1" dir="ltr">
                  {userId}
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  disabled={!config.status || saving}
                  onClick={() => void handleRemoveWhitelist(userId)}
                >
                  <Trash2 className="size-4" aria-hidden="true" />
                  Remove
                </Button>
              </li>
            ))
          )}
        </ul>
      </section>

      <div className="flex justify-end pt-2">
        <Button onClick={() => void handleSave()} disabled={saving}>
          {saving ? <RefreshCcw className="size-4 animate-spin" aria-hidden="true" /> : <Save className="size-4" aria-hidden="true" />}
          Save changes
        </Button>
      </div>
    </div>
  );
}
