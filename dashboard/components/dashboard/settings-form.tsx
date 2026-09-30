"use client";

import React, { useState } from "react";
import { Save, RefreshCcw, Command } from "lucide-react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

interface SettingsFormProps {
  initialPrefix: string;
  guildId: string;
}

export function SettingsForm({ initialPrefix, guildId }: SettingsFormProps) {
  const [prefix, setPrefix] = useState(initialPrefix);
  const [saving, setSaving] = useState(false);

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prefix || prefix.length > 10) {
      toast.error("Prefix must be between 1 and 10 characters.");
      return;
    }
    setSaving(true);
    try {
      await api.updatePrefix(guildId, prefix);
      toast.success("Prefix updated");
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : "Failed to update prefix";
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <form onSubmit={handleSave} className="space-y-4 rounded-md border border-line bg-surface-1 p-4">
      <div className="space-y-2">
        <label htmlFor="command-prefix" className="text-body font-medium text-fg-1 flex items-center gap-2">
          <Command className="size-4 text-fg-2" aria-hidden="true" />
          Command prefix
        </label>
        <Input
          id="command-prefix"
          value={prefix}
          onChange={(e) => setPrefix(e.target.value)}
          placeholder="e.g. !, ?, >>"
          maxLength={10}
          className="max-w-xs text-lg font-semibold"
        />
        <p className="text-caption text-fg-2">
          Triggers bot commands in this server (example: {prefix || ">"}help).
        </p>
      </div>
      <div className="flex justify-end pt-2">
        <Button type="submit" disabled={saving || !prefix}>
          {saving ? <RefreshCcw className="size-4 animate-spin" aria-hidden="true" /> : <Save className="size-4" aria-hidden="true" />}
          Save changes
        </Button>
      </div>
    </form>
  );
}
