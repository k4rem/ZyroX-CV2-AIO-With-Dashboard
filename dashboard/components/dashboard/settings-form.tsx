"use client";

import React, { useState } from "react";
import { toast } from "sonner";
import { SaveBar } from "@/components/settings/save-bar";
import { SettingRow } from "@/components/settings/setting-row";
import { api } from "@/lib/api";
import { Input } from "@/components/ui/input";

interface SettingsFormProps {
  initialPrefix: string;
  guildId: string;
}

export function SettingsForm({ initialPrefix, guildId }: SettingsFormProps) {
  const [saved, setSaved] = useState(initialPrefix);
  const [prefix, setPrefix] = useState(initialPrefix);
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!prefix || prefix.length > 10) {
      toast.error("Prefix must be between 1 and 10 characters.");
      return;
    }
    setSaving(true);
    try {
      await api.updatePrefix(guildId, prefix);
      setSaved(prefix);
      toast.success("Prefix updated");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to update prefix";
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (prefix !== saved) void handleSave();
      }}
    >
      <p className="max-w-xl text-small text-fg-3">
        This prefix starts bot commands in this server. Example: {(prefix || ">").trim()}help
      </p>
      <SettingRow label="Command prefix" description="1 to 10 characters. Applies after save." htmlFor="command-prefix">
        <Input
          id="command-prefix"
          value={prefix}
          onChange={(e) => setPrefix(e.target.value)}
          placeholder=">"
          maxLength={10}
          className="font-mono"
          dir="ltr"
        />
      </SettingRow>
      <SaveBar
        dirty={prefix !== saved}
        saving={saving}
        error={null}
        onSave={() => void handleSave()}
        onDiscard={() => setPrefix(saved)}
      />
    </form>
  );
}
