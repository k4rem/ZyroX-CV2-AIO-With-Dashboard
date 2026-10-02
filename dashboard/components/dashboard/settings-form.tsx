"use client";

import React, { useState } from "react";
import { toast } from "sonner";
import { SaveBar } from "@/components/settings/save-bar";
import { SettingGroup } from "@/components/settings/setting-group";
import { SettingRow } from "@/components/settings/setting-row";
import { SettingsInstrument } from "@/components/settings/settings-instrument";
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
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({});

  const handleSave = async () => {
    if (!prefix || prefix.length > 10) {
      setFieldErrors({ prefix: "Prefix must be between 1 and 10 characters." });
      return;
    }
    setFieldErrors({});
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

  const shown = (prefix || ">").trim();

  return (
    <form
      onSubmit={(event) => {
        event.preventDefault();
        if (prefix !== saved) void handleSave();
      }}
    >
      <SettingsInstrument summary={`Current prefix ${saved || ">"}. Commands start with that character.`}>
        <SettingGroup id="bot-commands" label="Bot commands" meta={<span dir="ltr">{saved || ">"}</span>}>
          <SettingRow label="Command prefix" description="1 to 10 characters. Applies after save." htmlFor="command-prefix">
            <Input
              id="command-prefix"
              value={prefix}
              onChange={(e) => {
                setPrefix(e.target.value);
                setFieldErrors({});
              }}
              placeholder=">"
              maxLength={10}
              className="font-mono"
              dir="ltr"
              aria-invalid={fieldErrors.prefix ? true : undefined}
              aria-describedby={fieldErrors.prefix ? "command-prefix-error" : undefined}
            />
            {fieldErrors.prefix ? (
              <p id="command-prefix-error" className="pt-1 text-caption text-danger">{fieldErrors.prefix}</p>
            ) : null}
          </SettingRow>
          <p className="pt-2 font-mono text-small text-fg-3" dir="ltr">
            {shown}help
          </p>
        </SettingGroup>
      </SettingsInstrument>
      <SaveBar
        dirty={prefix !== saved}
        saving={saving}
        error={null}
        fieldErrors={fieldErrors}
        onSave={() => void handleSave()}
        onDiscard={() => {
          setPrefix(saved);
          setFieldErrors({});
        }}
      />
    </form>
  );
}
