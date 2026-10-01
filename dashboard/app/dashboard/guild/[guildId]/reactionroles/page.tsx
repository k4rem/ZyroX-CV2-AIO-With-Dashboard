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
import { SettingGroup } from "@/components/settings/setting-group";
import { SettingRow } from "@/components/settings/setting-row";
import { SettingsInstrument } from "@/components/settings/settings-instrument";
import { api } from "@/lib/api";
import { roleSwatch } from "@/lib/modulePayloads";
import { Button } from "@/components/ui/button";
import { Combobox } from "@/components/ui/combobox";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";

export default function ReactionRolesPage({ params }: { params: { guildId: string } }) {
  const [loading, setLoading] = useState(true);
  const [loadingAction, setLoadingAction] = useState(false);
  const [config, setConfig] = useState<any>({ dm_enabled: true, roles: [] });
  const [roles, setRoles] = useState<any[]>([]);
  const [newRR, setNewRR] = useState({ message_id: "", emoji: "", role_id: "" });

  const fetchData = async () => {
    try {
      setLoading(true);
      const [configData, rolesData] = await Promise.all([
        api.getRR(params.guildId),
        api.getRoles(params.guildId),
      ]);
      setConfig(configData);
      setRoles(rolesData);
    } catch (error) {
      console.error("Failed to load RR:", error);
      toast.error("Failed to load reaction roles configuration");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [params.guildId]);

  const filteredRoles = roles.filter(r => r.name !== "@everyone");

  const toggleDM = async (val: boolean) => {
    try {
      await api.updateRR(params.guildId, { dm_enabled: val });
      setConfig({ ...config, dm_enabled: val });
      toast.success(`DM notifications ${val ? "enabled" : "disabled"}`);
    } catch {
      toast.error("Failed to update DM setting");
    }
  };

  const handleAdd = async () => {
    if (!newRR.message_id || !newRR.emoji || !newRR.role_id) {
      toast.error("Please fill in all fields");
      return;
    }
    setLoadingAction(true);
    try {
      await api.updateRR(params.guildId, {
        add_role: { message_id: newRR.message_id, emoji: newRR.emoji, role_id: newRR.role_id },
      });
      setConfig({
        ...config,
        roles: [...config.roles, { message_id: newRR.message_id, emoji: newRR.emoji, role_id: newRR.role_id }]
      });
      toast.success("Reaction role added");
      setNewRR({ message_id: "", emoji: "", role_id: "" });
    } catch {
      toast.error("Failed to add reaction role");
    } finally {
      setLoadingAction(false);
    }
  };

  const handleDelete = async (messageId: string, emoji: string) => {
    setLoadingAction(true);
    try {
      await api.updateRR(params.guildId, {
        remove_role_message_id: messageId,
        remove_role_emoji: emoji,
      });
      setConfig({
        ...config,
        roles: config.roles.filter((r: any) => !(String(r.message_id) === String(messageId) && r.emoji === emoji))
      });
      toast.success("Reaction role removed");
    } catch {
      toast.error("Failed to remove reaction role");
    } finally {
      setLoadingAction(false);
    }
  };

  if (loading) {
    return <div className="h-24 w-full animate-pulse rounded-md bg-surface-2" />;
  }

  return (
    <div>
      <PageHeader title="Reaction roles" description="Members take or lose a role by reacting to a message." />
      <SettingsInstrument
        wide
        summary={`${config.roles.length} listeners. ${config.dm_enabled ? "DM notifications on." : "DM notifications off."} Adding a listener also adds the reaction.`}
      >
      <SettingRow label="DM notifications" description="Message the member when this role is added or removed.">
        <Switch checked={config.dm_enabled} onCheckedChange={toggleDM} aria-label="DM notifications" />
      </SettingRow>
      <SettingGroup id="rr-add" label="Add listener">
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <label className="text-small text-fg-2">
            Message ID
            <Input
              value={newRR.message_id}
              onChange={(event) => setNewRR({ ...newRR, message_id: event.target.value.trim() })}
              placeholder="Snowflake"
              className="mt-1 font-mono"
              dir="ltr"
              inputMode="numeric"
            />
          </label>
          <label className="text-small text-fg-2">
            Emoji
            <Input
              value={newRR.emoji}
              onChange={(event) => setNewRR({ ...newRR, emoji: event.target.value })}
              className="mt-1"
            />
          </label>
          <label className="text-small text-fg-2">
            Role
            <span className="mt-1 block">
              <Combobox
                value={newRR.role_id || null}
                onValueChange={(value) => setNewRR({ ...newRR, role_id: value ?? "" })}
                options={filteredRoles.map((role) => ({
                  value: String(role.id),
                  label: role.name,
                  swatch: roleSwatch(role.color),
                }))}
                placeholder="Select a role"
                searchLabel="Search roles"
              />
            </span>
          </label>
        </div>
        <div className="mt-3">
          <Button type="button" variant="secondary" onClick={() => void handleAdd()} disabled={loadingAction}>
            Add listener
          </Button>
        </div>
      </SettingGroup>
      <SettingGroup id="rr-active" label="Listeners" meta={String(config.roles.length)}>
        <ul className="mt-2 border-t border-line">
          {config.roles.length === 0 ? (
            <li className="py-3 text-small text-fg-3" dir="auto">
              No listeners yet. Add a message ID, emoji, and role above.
            </li>
          ) : (
            config.roles.map((rr: { message_id: string; emoji: string; role_id: string }, index: number) => {
              const role = filteredRoles.find((item) => String(item.id) === String(rr.role_id));
              return (
                <li key={`${rr.message_id}-${rr.emoji}-${index}`} className="grid items-center gap-2 border-b border-line-subtle py-2 sm:grid-cols-[8rem_4rem_minmax(0,1fr)_auto]">
                  <span className="font-mono text-small text-fg-2" dir="ltr">{rr.message_id}</span>
                  <span className="text-body text-fg-1">{rr.emoji}</span>
                  <span className="inline-flex min-w-0 items-center gap-2 text-body text-fg-1">
                    <span className="size-2.5 shrink-0 rounded-full border border-line" style={{ background: roleSwatch(role?.color) ?? "transparent" }} />
                    <span className="truncate">{role?.name ?? "Unknown role"}</span>
                  </span>
                  <Button type="button" variant="danger-secondary" size="sm" disabled={loadingAction} onClick={() => void handleDelete(String(rr.message_id), rr.emoji)}>
                    Remove
                  </Button>
                </li>
              );
            })
          )}
        </ul>
      </SettingGroup>
      </SettingsInstrument>
    </div>
  );
}
