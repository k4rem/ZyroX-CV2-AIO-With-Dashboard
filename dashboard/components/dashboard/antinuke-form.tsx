"use client";

import React, { useState } from "react";
import { toast } from "sonner";
import { SaveBar } from "@/components/settings/save-bar";
import { SettingGroup } from "@/components/settings/setting-group";
import { SettingRow } from "@/components/settings/setting-row";
import { SettingsInstrument } from "@/components/settings/settings-instrument";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { StatusLabel } from "@/components/ui/status";
import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api";
import { normalizeSnowflakeInput } from "@/lib/snowflake";
import type { AntiNukeConfig } from "@/types/api";

export function AntiNukeForm({ initialConfig, guildId }: { initialConfig: AntiNukeConfig; guildId: string }) {
  const [savedStatus, setSavedStatus] = useState(Boolean(initialConfig.status));
  const [status, setStatus] = useState(Boolean(initialConfig.status));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [wlInput, setWlInput] = useState("");
  const [whitelistedUsers, setWhitelistedUsers] = useState<string[]>(initialConfig.whitelisted_users || []);
  const dirty = status !== savedStatus;

  const handleSave = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.updateAntiNuke(guildId, { status });
      setSavedStatus(status);
      toast.success("Protection switch saved");
    } catch {
      setError("Could not save the protection switch.");
      toast.error("Could not save the protection switch");
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
      await api.updateAntiNuke(guildId, { status: savedStatus, add_whitelist: uid });
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
      await api.updateAntiNuke(guildId, { status: savedStatus, remove_whitelist: userId });
      setWhitelistedUsers(whitelistedUsers.filter((id) => id !== userId));
      toast.success("User removed from whitelist");
    } catch {
      toast.error("Failed to remove user");
    } finally {
      setSaving(false);
    }
  };

  return (
    <SettingsInstrument
      summary={`${savedStatus ? "On" : "Off"} · ${whitelistedUsers.length} whitelisted ${whitelistedUsers.length === 1 ? "user" : "users"}.`}
    >
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 border border-line-subtle px-3 py-2">
        <StatusLabel status={savedStatus ? "online" : "disabled"}>{savedStatus ? "Protection on" : "Protection off"}</StatusLabel>
        <span className="font-mono text-small text-fg-2" dir="ltr">
          {whitelistedUsers.length} whitelisted
        </span>
      </div>

      <SettingGroup id="antinuke-config" label="Protection">
        <SettingRow
          label="Master switch"
          description="Turns the current antinuke checks on or off. Save the switch before changing the whitelist."
        >
          <Switch checked={status} onCheckedChange={setStatus} aria-label="Antinuke enabled" />
        </SettingRow>
      </SettingGroup>

      <SettingGroup id="antinuke-whitelist" label="Whitelist" meta={String(whitelistedUsers.length)}>
        <p className="mt-1 text-small text-fg-3" dir="auto">
          Trusted user IDs are exempt. Add and remove apply immediately.
        </p>
        <div className="mt-3 flex flex-col gap-2 sm:flex-row">
          <Input
            value={wlInput}
            onChange={(e) => setWlInput(e.target.value)}
            placeholder="Discord user ID"
            dir="ltr"
            className="font-mono"
            disabled={dirty || saving}
            inputMode="numeric"
          />
          <Button
            type="button"
            variant="secondary"
            onClick={() => void handleAddWhitelist()}
            disabled={dirty || saving}
          >
            Add
          </Button>
        </div>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full border-collapse text-start">
            <thead>
              <tr className="border-b border-line text-caption text-fg-3">
                <th className="py-2 pe-3 text-start font-medium">User ID</th>
                <th className="py-2 text-end font-medium"> </th>
              </tr>
            </thead>
            <tbody>
              {whitelistedUsers.length === 0 ? (
                <tr>
                  <td colSpan={2} className="py-3 text-small text-fg-3" dir="auto">
                    No whitelisted users.
                  </td>
                </tr>
              ) : (
                whitelistedUsers.map((userId) => (
                  <tr key={userId} className="border-b border-line-subtle">
                    <td className="py-2 pe-3 font-mono text-body text-fg-1" dir="ltr">
                      {userId}
                    </td>
                    <td className="py-2 text-end">
                      <Button
                        type="button"
                        variant="danger-secondary"
                        size="sm"
                        disabled={dirty || saving}
                        onClick={() => void handleRemoveWhitelist(userId)}
                      >
                        Remove
                      </Button>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </SettingGroup>

      <SaveBar
        dirty={dirty}
        saving={saving}
        error={error}
        onSave={() => void handleSave()}
        onDiscard={() => {
          setStatus(savedStatus);
          setError(null);
        }}
      />
    </SettingsInstrument>
  );
}
