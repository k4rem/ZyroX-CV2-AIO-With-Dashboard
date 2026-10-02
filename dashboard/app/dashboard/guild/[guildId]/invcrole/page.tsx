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
import { SettingGroup } from "@/components/settings/setting-group";
import { SettingRow } from "@/components/settings/setting-row";
import { SettingsInstrument } from "@/components/settings/settings-instrument";
import { api } from "@/lib/api";
import { draftsDiffer } from "@/lib/modulePayloads";
import { RolePicker } from "@/components/discord/channel-picker";
import { Switch } from "@/components/ui/switch";

export default function InvcRolePage({ params }: { params: { guildId: string } }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [roles, setRoles] = useState<any[]>([]);
  const [botRole, setBotRole] = useState<{ top_role_id: string; top_role_position: number; manage_roles: boolean } | null>(null);
  const [saved, setSaved] = useState<any>({ role_id: null, enabled: false });
  const [config, setConfig] = useState<any>({ role_id: null, enabled: false });

  const fetchData = async () => {
    try {
      setLoading(true);
      const [configData, rolesData, health] = await Promise.all([
        api.getInvcRole(params.guildId),
        api.getRoles(params.guildId),
        api.getRuntimeHealth(params.guildId).catch(() => null),
      ]);
      setConfig(configData);
      setSaved({ role_id: configData?.role_id ?? null, enabled: Boolean(configData?.enabled) });
      setRoles(rolesData);
      setBotRole(health?.bot ?? null);
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
      <SettingsInstrument
        summary={`${config.enabled ? "On" : "Off"} · ${config.role_id ? "role saved" : "no role"}. Turning this off keeps the selected role.`}
      >
      <SettingGroup id="voice-role" label="Voice state">
      <SettingRow label="Enabled" description={config.enabled ? "Monitoring voice channels." : "Off. The selected role stays saved."}>
        <Switch
          checked={Boolean(config.enabled)}
          onCheckedChange={(checked) => setConfig({ ...config, enabled: checked })}
          aria-label="Voice role enabled"
        />
      </SettingRow>
      <SettingRow label="Assigned role" description="Must sit below the bot role." htmlFor="invc-role">
        <RolePicker
          roles={filteredRoles.map((role) => ({
            id: String(role.id),
            name: role.name,
            position: role.position,
            managed: Boolean(role.managed),
          }))}
          value={config.role_id ? String(config.role_id) : ""}
          onChange={(id) => setConfig({ ...config, role_id: id || null })}
          botPosition={botRole?.top_role_position ?? null}
          botRoleId={botRole?.top_role_id ?? null}
          manageRoles={botRole?.manage_roles ?? null}
          intent="mutate"
          allowEmpty
        />
      </SettingRow>
      </SettingGroup>
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
      </SettingsInstrument>
    </div>
  );
}
