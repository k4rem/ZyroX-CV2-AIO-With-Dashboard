"use client";

import React, { useEffect, useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { InlineBanner } from "@/components/ui/state";
import { api, ApiError } from "@/lib/api";
import { SaveBar } from "@/components/settings/save-bar";
import { SettingGroup } from "@/components/settings/setting-group";
import { SettingRow } from "@/components/settings/setting-row";
import { SettingsInstrument } from "@/components/settings/settings-instrument";
import { Combobox } from "@/components/ui/combobox";
import { Readout } from "@/components/ui/readout";
import { StatusLabel } from "@/components/ui/status";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";

type VerificationState = {
  enabled: boolean;
  unverified_role_id: string | null;
  verified_role_id: string | null;
  channel_id: string | null;
  grace_seconds: number;
  message: string;
  protected_category_ids: string[];
  counts: { grace: number; unverified: number; verified: number; exempt: number };
};

export default function VerificationPage({ params }: { params: { guildId: string } }) {
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [channels, setChannels] = useState<Array<{ id: string; name: string; type: string }>>([]);
  const [roles, setRoles] = useState<Array<{ id: string; name: string }>>([]);
  const [saved, setSaved] = useState<VerificationState | null>(null);
  const [draft, setDraft] = useState<VerificationState | null>(null);
  const [canEnable, setCanEnable] = useState(false);

  useEffect(() => {
    let cancel = false;
    (async () => {
      try {
        const [config, channelList, roleList] = await Promise.all([
          api.getVerification(params.guildId),
          api.getChannels(params.guildId),
          api.getRoles(params.guildId),
        ]);
        if (cancel) return;
        const publishReady = Boolean(config?.can_enable);
        setCanEnable(publishReady);
        const next: VerificationState = {
          enabled: publishReady && Boolean(config?.enabled),
          unverified_role_id: config?.unverified_role_id ?? null,
          verified_role_id: config?.verified_role_id ?? null,
          channel_id: config?.channel_id ?? null,
          grace_seconds: Number(config?.grace_seconds ?? 604800),
          message: config?.message ?? "",
          protected_category_ids: config?.protected_category_ids ?? [],
          counts: config?.counts ?? { grace: 0, unverified: 0, verified: 0, exempt: 0 },
        };
        setSaved(next);
        setDraft(next);
        setChannels(Array.isArray(channelList) ? channelList : []);
        setRoles(Array.isArray(roleList) ? roleList.filter((role) => role.name !== "@everyone") : []);
      } catch {
        if (!cancel) setError("Verification state could not be loaded.");
      } finally {
        if (!cancel) setLoading(false);
      }
    })();
    return () => {
      cancel = true;
    };
  }, [params.guildId]);

  if (loading) return <div className="h-24 w-full animate-pulse rounded-md bg-surface-2" />;
  if (!draft || !saved) return <p className="text-small text-fg-3">{error || "Verification is unavailable."}</p>;

  const dirty = JSON.stringify(draft) !== JSON.stringify(saved);
  const categories = channels.filter((channel) => channel.type === "4");
  const texts = channels.filter((channel) => channel.type === "0");
  const roleOptions = roles.map((role) => ({ value: role.id, label: role.name }));
  const channelOptions = texts.map((channel) => ({ value: channel.id, label: channel.name, glyph: "text" as const }));

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      const result = await api.updateVerification(params.guildId, {
        enabled: draft.enabled,
        unverified_role_id: draft.unverified_role_id,
        verified_role_id: draft.verified_role_id,
        verification_channel_id: draft.channel_id,
        grace_seconds: draft.grace_seconds,
        message: draft.message,
        protected_category_ids: draft.protected_category_ids,
        verification_method: "button",
      });
      const next = { ...draft, ...(result || {}), counts: result?.counts ?? draft.counts, enabled: Boolean(result?.can_enable) && Boolean(result?.enabled) };
      setSaved(next);
      setDraft(next);
      toast.success("Verification saved");
    } catch (err) {
      const message = err instanceof ApiError && err.message
        ? err.message
        : "Could not save. Enable needs the unverified role, at least one category, and the bot above that role.";
      setError(message);
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  const toggleCategory = (id: string) => {
    setDraft({
      ...draft,
      protected_category_ids: draft.protected_category_ids.includes(id)
        ? draft.protected_category_ids.filter((item) => item !== id)
        : [...draft.protected_category_ids, id],
    });
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="Verification"
        description="Unverified members are denied the categories you choose. The verified role is only a status, not a permission key."
      />
      {!canEnable ? (
        <InlineBanner tone="warning" title="Verification cannot be enabled until a verification message is published.">
          Publishing a verify message is not available yet, so the gate stays off.
        </InlineBanner>
      ) : null}
      <SettingsInstrument wide summary={draft.enabled ? "Gate on. New joins are unverified. Existing members stay in grace." : "Gate off. No overwrites are applied."}>
        <dl className="grid grid-cols-2 border border-line-subtle sm:grid-cols-4">
          <Readout label="Status">
            <StatusLabel status={draft.enabled ? "online" : "disabled"}>{draft.enabled ? "On" : "Off"}</StatusLabel>
          </Readout>
          <Readout label="Grace">{draft.counts.grace}</Readout>
          <Readout label="Unverified">{draft.counts.unverified}</Readout>
          <Readout label="Verified">{draft.counts.verified}</Readout>
        </dl>

        <SettingGroup id="verification-gate" label="Gate">
          <SettingRow label="Enabled" description={canEnable ? "Off leaves every overwrite untouched. On denies view for the unverified role on the selected categories." : "Verification cannot be enabled until a verification message is published."}>
            <Switch checked={draft.enabled} disabled={!canEnable} onCheckedChange={(enabled) => { if (canEnable) setDraft({ ...draft, enabled }); }} aria-label="Verification enabled" />
          </SettingRow>
          <SettingRow label="Unverified role" description="This role is denied the protected categories. It is removed after the member passes.">
            <Combobox id="unverified-role" value={draft.unverified_role_id} options={roleOptions} onValueChange={(unverified_role_id) => setDraft({ ...draft, unverified_role_id })} placeholder="Choose a role" />
          </SettingRow>
          <SettingRow label="Status role" description="Optional. It does not grant channel access.">
            <Combobox id="verified-role" value={draft.verified_role_id} options={roleOptions} onValueChange={(verified_role_id) => setDraft({ ...draft, verified_role_id })} placeholder="None" />
          </SettingRow>
          <SettingRow label="Channel" description="Verification cannot be enabled until a verification message is published.">
            <Combobox id="verify-channel" value={draft.channel_id} options={channelOptions} onValueChange={(channel_id) => setDraft({ ...draft, channel_id })} placeholder="Choose a channel" />
          </SettingRow>
        </SettingGroup>

        <SettingGroup id="verification-categories" label="Protected categories" meta={String(draft.protected_category_ids.length)}>
          {categories.length === 0 ? (
            <p className="text-small text-fg-3">No categories are available from Discord right now.</p>
          ) : (
            <ul className="space-y-1">
              {categories.map((category) => (
                <li key={category.id}>
                  <label className="flex items-center gap-2 text-small text-fg-1">
                    <input
                      type="checkbox"
                      checked={draft.protected_category_ids.includes(category.id)}
                      onChange={() => toggleCategory(category.id)}
                    />
                    {category.name}
                  </label>
                </li>
              ))}
            </ul>
          )}
        </SettingGroup>

        <SettingGroup id="verification-grace" label="Existing members">
          <SettingRow label="Grace" description="Members who joined before the gate stay as they are until this many hours pass.">
            <input
              className="w-24 border border-line-subtle bg-surface-1 px-2 py-1 font-mono text-small"
              inputMode="numeric"
              value={Math.round(draft.grace_seconds / 3600)}
              onChange={(event) => setDraft({ ...draft, grace_seconds: Math.max(0, Number(event.target.value) || 0) * 3600 })}
              aria-label="Grace hours"
            />
          </SettingRow>
          <Textarea
            value={draft.message}
            onChange={(event) => setDraft({ ...draft, message: event.target.value })}
            placeholder="Why verification exists, and that no Discord password is requested."
          />
        </SettingGroup>

        <SaveBar
          dirty={dirty}
          saving={saving}
          error={error}
          onSave={() => void save()}
          onDiscard={() => {
            setDraft(saved);
            setError(null);
          }}
        />
      </SettingsInstrument>
    </div>
  );
}
