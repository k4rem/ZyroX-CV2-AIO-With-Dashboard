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
import { SettingsInstrument } from "@/components/settings/settings-instrument";
import { api } from "@/lib/api";
import { draftsDiffer } from "@/lib/modulePayloads";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";

export default function AutoReactPage({ params }: { params: { guildId: string } }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState<any[]>([]);
  const [config, setConfig] = useState<any>({ triggers: [] });

  const fetchData = async () => {
    try {
      setLoading(true);
      const configData = await api.getAutoReact(params.guildId);
      setConfig(configData);
      setSaved(configData?.triggers ?? []);
    } catch (error) {
      console.error("Failed to fetch auto react data:", error);
      toast.error("Failed to load auto react configuration");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchData(); }, [params.guildId]);

  const handleSave = async () => {
    setSaving(true);
    const promise = api.updateAutoReact(params.guildId, { triggers: config.triggers });
    toast.promise(promise, {
      loading: 'Saving auto react configuration...',
      success: 'Auto react settings saved!',
      error: 'Failed to save auto react config',
    });
    try {
      await promise;
      setSaved(config.triggers);
      setError(null);
    } catch {
      setError("Could not save auto react.");
    } finally {
      setSaving(false);
    }
  };

  const addTrigger = () => {
    if (config.triggers.length >= 10) {
      toast.error("Maximum 10 triggers allowed");
      return;
    }
    setConfig({ ...config, triggers: [...config.triggers, { trigger: "", emojis: "" }] });
  };

  const removeTrigger = (index: number) => {
    const newTriggers = [...config.triggers];
    newTriggers.splice(index, 1);
    setConfig({ ...config, triggers: newTriggers });
  };

  const updateTrigger = (index: number, field: string, value: string) => {
    const newTriggers = [...config.triggers];
    newTriggers[index] = { ...newTriggers[index], [field]: value };
    setConfig({ ...config, triggers: newTriggers });
  };

  if (loading) {
    return <div className="h-24 w-full animate-pulse rounded-md bg-surface-2" />;
  }

  const dirty = draftsDiffer(saved, config.triggers);

  return (
    <div>
      <PageHeader title="Auto react" description="React when a message contains a trigger word.">
        <Button type="button" variant="secondary" onClick={addTrigger} disabled={config.triggers.length >= 10}>
          Add trigger
        </Button>
      </PageHeader>
      <SettingsInstrument summary={`${config.triggers.length} of 10 triggers. Each trigger is one word. Custom emoji must belong to this server.`}>
      <SettingGroup id="autoreact-triggers" label="Triggers" meta={`${config.triggers.length} of 10`}>
        {config.triggers.length === 0 ? (
          <p className="py-3 text-small text-fg-3" dir="auto">
            No triggers yet. Add a word and an emoji, then save.
          </p>
        ) : (
          <ul className="mt-2 border-t border-line">
            {config.triggers.map((item: { trigger: string; emojis: string }, index: number) => (
              <li key={index} className="grid items-end gap-3 border-b border-line-subtle py-3 md:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]">
                <label className="text-small text-fg-2">
                  Word
                  <Input value={item.trigger} onChange={(event) => updateTrigger(index, "trigger", event.target.value)} className="mt-1" />
                </label>
                <label className="text-small text-fg-2">
                  Emoji
                  <Input value={item.emojis} onChange={(event) => updateTrigger(index, "emojis", event.target.value)} className="mt-1" />
                </label>
                <Button type="button" variant="danger-secondary" size="sm" onClick={() => removeTrigger(index)}>
                  Remove
                </Button>
              </li>
            ))}
          </ul>
        )}
      </SettingGroup>
      <SaveBar
        dirty={dirty}
        saving={saving}
        error={error}
        onSave={() => void handleSave()}
        onDiscard={() => {
          setConfig({ ...config, triggers: saved });
          setError(null);
        }}
      />
      </SettingsInstrument>
    </div>
  );
}
