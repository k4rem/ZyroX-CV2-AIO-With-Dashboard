/**
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║                                                                  ║
 * ║   ░█▀▀░█▀█░█▀▄░█▀▀░█░█   ░█▀▄░█▀▀░█░█░█▀▀                     ║
 * ║   ░█░░░█░█░█░█░█▀▀░▄▀▄   ░█░█░█▀▀░▀▄▀░▀▀█                     ║
 * ║   ░▀▀▀░▀▀▀░▀▀░░▀▀▀░▀░▀   ░▀▀░░▀▀▀░░▀░░▀▀▀                     ║
 * ║                                                                  ║
 * ║           © 2026 CodeX Devs — All Rights Reserved               ║
 * ║                                                                  ║
 * ║   discord  ──  https://discord.gg/codexdev                      ║
 * ║   youtube  ──  https://youtube.com/@CodeXDevs                   ║
 * ║   github   ──  https://github.com/RayExo                        ║
 * ║                                                                  ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

"use client";

import React, { useState, useEffect } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { SaveBar } from "@/components/settings/save-bar";
import { SettingRow } from "@/components/settings/setting-row";
import { api } from "@/lib/api";
import { draftsDiffer, roleSwatch } from "@/lib/modulePayloads";
import { Combobox } from "@/components/ui/combobox";
import { Switch } from "@/components/ui/switch";

export default function InvcRolePage({ params }: { params: { guildId: string } }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [roles, setRoles] = useState<any[]>([]);
  const [saved, setSaved] = useState<any>({ role_id: null, enabled: false });
  const [config, setConfig] = useState<any>({ role_id: null, enabled: false });

  const fetchData = async () => {
    try {
      setLoading(true);
      const [configData, rolesData] = await Promise.all([
        api.getInvcRole(params.guildId),
        api.getRoles(params.guildId),
      ]);
      setConfig(configData);
      setSaved({ role_id: configData?.role_id ?? null, enabled: Boolean(configData?.enabled) });
      setRoles(rolesData);
    } catch (error) {
      console.error("Failed to fetch InvcRole data:", error);
      toast.error("Failed to load Voice Role configuration");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [params.guildId]);

  const handleSave = async () => {
    setSaving(true);
    const promise = api.updateInvcRole(params.guildId, { 
      role_id: config.role_id,
      enabled: config.enabled
    });
    toast.promise(promise, {
      loading: 'Saving Voice Role configuration...',
      success: 'Voice Role settings saved!',
      error: 'Failed to save Voice Role config',
    });
    try {
      await promise;
      setSaved({ role_id: config.role_id, enabled: config.enabled });
      setError(null);
    } catch {
      setError("Could not save the voice role.");
    } finally {
      setSaving(false);
    }
  };

  const filteredRoles = roles.filter(r => r.name !== "@everyone");

  if (loading) {
    return <div className="h-24 w-full animate-pulse rounded-md bg-surface-2" />;
  }

  const dirty = draftsDiffer(
    { role_id: saved.role_id ?? null, enabled: Boolean(saved.enabled) },
    { role_id: config.role_id ?? null, enabled: Boolean(config.enabled) },
  );

  return (
    <div>
      <PageHeader title="Voice role" description="Assign a role while a member is in a voice channel." />
      <p className="mb-2 max-w-2xl text-small text-fg-3">
        The role is added on join and removed when they leave every voice channel. Turning this off keeps the selected role.
      </p>
      <SettingRow label="Enabled" description={config.enabled ? "Monitoring voice channels." : "Off. The selected role stays saved."}>
        <Switch
          checked={Boolean(config.enabled)}
          onCheckedChange={(checked) => setConfig({ ...config, enabled: checked })}
          aria-label="Voice role enabled"
        />
      </SettingRow>
      <SettingRow label="Role" description="Must sit below the bot role." htmlFor="invc-role">
        <Combobox
          id="invc-role"
          value={config.role_id ? String(config.role_id) : null}
          onValueChange={(value) => setConfig({ ...config, role_id: value })}
          options={[
            { value: "", label: "No role" },
            ...filteredRoles.map((role) => ({
              value: String(role.id),
              label: role.name,
              swatch: roleSwatch(role.color),
            })),
          ]}
          placeholder="Select a role"
          searchLabel="Search roles"
        />
      </SettingRow>
      <SaveBar
        dirty={dirty}
        saving={saving}
        error={error}
        onSave={() => void handleSave()}
        onDiscard={() => {
          setConfig({ ...config, ...saved });
          setError(null);
        }}
      />
    </div>
  );
}
