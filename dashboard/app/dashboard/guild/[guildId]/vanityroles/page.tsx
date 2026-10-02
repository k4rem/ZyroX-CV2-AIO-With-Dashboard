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
import { InlineBanner } from "@/components/ui/state";
import { SettingGroup } from "@/components/settings/setting-group";
import { SettingsInstrument } from "@/components/settings/settings-instrument";
import { api } from "@/lib/api";
import { roleSwatch } from "@/lib/modulePayloads";
import { Button } from "@/components/ui/button";
import { Combobox } from "@/components/ui/combobox";
import { Input } from "@/components/ui/input";

export default function VanityRolesPage({ params }: { params: { guildId: string } }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [roles, setRoles] = useState<any[]>([]);
  const [channels, setChannels] = useState<any[]>([]);
  const [setups, setSetups] = useState<any[]>([]);
  const [newSetup, setNewSetup] = useState({ vanity: "", role_id: "", log_channel_id: "" });

  const fetchData = async () => {
    try {
      setLoading(true);
      const [setupsData, rolesData, channelsData] = await Promise.all([
        api.getVanityRoles(params.guildId),
        api.getRoles(params.guildId),
        api.getChannels(params.guildId),
      ]);
      setSetups(setupsData);
      setRoles(rolesData);
      setChannels(channelsData);
    } catch (error) {
      console.error("Failed to fetch vanity roles data:", error);
      toast.error("Failed to load vanity roles configuration");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [params.guildId]);

  const textChannels = channels.filter(c => c.type === "0" || c.type === 0);
  const filteredRoles = roles.filter(r => r.name !== "@everyone");

  const handleAdd = async () => {
    if (!newSetup.vanity || !newSetup.role_id || !newSetup.log_channel_id) {
      toast.error("Please fill in all fields");
      return;
    }
    setSaving(true);
    try {
      await api.addVanityRole(params.guildId, {
        vanity: newSetup.vanity,
        role_id: newSetup.role_id,
        log_channel_id: newSetup.log_channel_id,
      });
      toast.success("Vanity role setup added!");
      setNewSetup({ vanity: "", role_id: "", log_channel_id: "" });
      fetchData();
    } catch (error) {
      toast.error("Failed to add vanity role setup");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (vanity: string) => {
    try {
      await api.deleteVanityRole(params.guildId, vanity);
      toast.success("Vanity role setup deleted");
      fetchData();
    } catch (error) {
      toast.error("Failed to delete vanity role setup");
    }
  };

  if (loading) {
    return <div className="h-24 w-full animate-pulse rounded-md bg-surface-2" />;
  }

  return (
    <div className="space-y-4">
      <PageHeader title="Vanity roles" description="Saved setups stay stored. Member-status matching is not running." />
      <InlineBanner tone="warning">
        Vanity Roles is temporarily unavailable while member-status matching is being rebuilt.
      </InlineBanner>
      <SettingsInstrument wide summary={`${setups.length} saved. Automation is off, so no roles are added or removed.`}>
      <SettingGroup id="vanity-add" label="Add setup">
        <div className="mt-3 grid gap-3 md:grid-cols-3">
          <label className="text-small text-fg-2">
            Vanity text
            <Input
              value={newSetup.vanity}
              onChange={(event) => setNewSetup({ ...newSetup, vanity: event.target.value })}
              placeholder=".gg/example"
              className="mt-1"
              disabled
            />
          </label>
          <label className="text-small text-fg-2">
            Role
            <span className="mt-1 block">
              <Combobox
                value={newSetup.role_id || null}
                onValueChange={(value) => setNewSetup({ ...newSetup, role_id: value ?? "" })}
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
          <label className="text-small text-fg-2">
            Log channel
            <span className="mt-1 block">
              <Combobox
                value={newSetup.log_channel_id || null}
                onValueChange={(value) => setNewSetup({ ...newSetup, log_channel_id: value ?? "" })}
                options={textChannels.map((channel) => ({
                  value: String(channel.id),
                  label: channel.name,
                  glyph: "text" as const,
                }))}
                placeholder="Select a channel"
                searchLabel="Search channels"
              />
            </span>
          </label>
        </div>
        <div className="mt-3">
          <Button type="button" variant="secondary" onClick={() => void handleAdd()} disabled>
            Add setup
          </Button>
        </div>
      </SettingGroup>
      <SettingGroup id="vanity-active" label="Saved setups" meta={String(setups.length)}>
        <ul className="mt-2 border-t border-line">
          {setups.length === 0 ? (
            <li className="py-3 text-small text-fg-3" dir="auto">
              No saved setups. New setups cannot be added until member-status matching is rebuilt.
            </li>
          ) : (
            setups.map((setup, index) => {
              const role = filteredRoles.find((item) => String(item.id) === String(setup.role_id));
              const channel = channels.find((item) => String(item.id) === String(setup.log_channel_id));
              return (
                <li key={`${setup.vanity}-${index}`} className="grid items-center gap-2 border-b border-line-subtle py-2 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_minmax(0,1fr)_auto]">
                  <span className="truncate text-body text-fg-1">{setup.vanity}</span>
                  <span className="inline-flex min-w-0 items-center gap-2 text-small text-fg-2">
                    <span className="size-2.5 shrink-0 rounded-full border border-line" style={{ background: roleSwatch(role?.color) ?? "transparent" }} />
                    <span className="truncate">{role?.name ?? "Unknown role"}</span>
                  </span>
                  <span className="truncate text-small text-fg-3">#{channel?.name ?? "Unknown channel"}</span>
                  <Button type="button" variant="danger-secondary" size="sm" onClick={() => void handleDelete(setup.vanity)}>
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
