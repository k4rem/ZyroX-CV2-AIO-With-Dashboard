"use client";

import React, { useState } from "react";
import { toast } from "sonner";
import { SaveBar } from "@/components/settings/save-bar";
import { SettingGroup } from "@/components/settings/setting-group";
import { SettingRow } from "@/components/settings/setting-row";
import { SettingsInstrument } from "@/components/settings/settings-instrument";
import { StatusLabel } from "@/components/ui/status";
import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api";

export type SecuritySummary = {
  guild_id: string;
  human_mode: "OFF" | "OBSERVE" | "ENFORCE";
  bot_mode: "OFF" | "OBSERVE" | "ENFORCE";
  effective_human_mode: string;
  effective_bot_mode: string;
  enforce_locked: boolean;
  version: number;
  permission_health: string;
  policies: Array<{
    action_class: string;
    enabled: boolean;
    threshold: number;
    window_s: number;
    containment_eligible: boolean;
    threshold_status: string;
  }>;
  trusted_actors: Array<{ subject_id: string; kind: string; scopes: string[] }>;
  maintenance: { reason: string; ends_at: string } | null;
  incidents: Array<{ id: string; status: string; engine: string; severity: string; subject_id: string | null }>;
  quarantines: Array<{ user_id: string; status: string; prior_role_ids: string[] }>;
  ops: { pending_alerts: number };
};

export function SecurityPanel({
  initial,
  guildId,
  isRoot,
}: {
  initial: SecuritySummary;
  guildId: string;
  isRoot: boolean;
}) {
  const [data, setData] = useState(initial);
  const [humanOn, setHumanOn] = useState(initial.human_mode !== "OFF");
  const [botOn, setBotOn] = useState(initial.bot_mode !== "OFF");
  const [saving, setSaving] = useState(false);
  const dirty = humanOn !== (data.human_mode !== "OFF") || botOn !== (data.bot_mode !== "OFF");

  const save = async () => {
    setSaving(true);
    try {
      let version = data.version;
      if (humanOn !== (data.human_mode !== "OFF")) {
        const row = await api.setSecurityMode(guildId, {
          subsystem: "human",
          mode: humanOn ? "OBSERVE" : "OFF",
          expected_version: version,
        });
        version = row.version;
      }
      if (botOn !== (data.bot_mode !== "OFF")) {
        const row = await api.setSecurityMode(guildId, {
          subsystem: "bot",
          mode: botOn ? "OBSERVE" : "OFF",
          expected_version: version,
        });
        version = row.version;
      }
      const next = await api.getSecurity(guildId);
      if (next) setData(next);
      toast.success("Protection mode saved");
    } catch {
      toast.error("Could not save protection mode");
    } finally {
      setSaving(false);
    }
  };

  return (
    <SettingsInstrument
      summary={`${data.effective_human_mode} human · ${data.effective_bot_mode} bots · ${data.incidents.length} recent incidents.`}
    >
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2 border border-line-subtle px-3 py-2">
        <StatusLabel status={data.effective_human_mode === "OFF" ? "disabled" : "online"}>
          Human {data.effective_human_mode}
        </StatusLabel>
        <StatusLabel status={data.effective_bot_mode === "OFF" ? "disabled" : "online"}>
          Bots {data.effective_bot_mode}
        </StatusLabel>
        <span className="font-mono text-small text-fg-2">ENFORCE locked</span>
        <span className="font-mono text-small text-fg-2">{data.ops.pending_alerts} ops alerts waiting</span>
      </div>

      <SettingGroup id="security-mode" label="Mode">
        <SettingRow label="Human protection" description="OBSERVE records and alerts. It does not remove roles.">
          <Switch checked={humanOn} onCheckedChange={setHumanOn} disabled={!isRoot} aria-label="Human protection" />
        </SettingRow>
        <SettingRow label="Bot protection" description="A bot add is recorded and alerted. The inviter is not punished.">
          <Switch checked={botOn} onCheckedChange={setBotOn} disabled={!isRoot} aria-label="Bot protection" />
        </SettingRow>
      </SettingGroup>

      <SettingGroup id="security-health" label="Health">
        <p className="text-small text-fg-2">Permission health: {data.permission_health}. View Audit Log is observability only.</p>
        <p className="text-small text-fg-2">
          Maintenance: {data.maintenance ? `${data.maintenance.reason} until ${data.maintenance.ends_at}` : "none"}
        </p>
      </SettingGroup>

      <SettingGroup id="security-policy" label="Rules" meta={String(data.policies.length)}>
        <ul className="space-y-1 font-mono text-small text-fg-2">
          {data.policies.map((row) => (
            <li key={row.action_class}>
              {row.action_class} · {row.threshold}/{row.window_s}s · {row.threshold_status}
              {row.containment_eligible ? " · eligible" : ""}
            </li>
          ))}
        </ul>
      </SettingGroup>

      <SettingGroup id="security-trust" label="Trusted actors" meta={String(data.trusted_actors.length)}>
        {data.trusted_actors.length === 0 ? (
          <p className="text-small text-fg-3">No trusted actors. Legacy whitelist is not imported.</p>
        ) : (
          <ul className="font-mono text-small text-fg-2">
            {data.trusted_actors.map((row) => (
              <li key={row.subject_id}>
                {row.subject_id} · {row.kind}
              </li>
            ))}
          </ul>
        )}
      </SettingGroup>

      <SettingGroup id="security-incidents" label="Incidents" meta={String(data.incidents.length)}>
        {data.incidents.length === 0 ? (
          <p className="text-small text-fg-3">No incidents stored for this server.</p>
        ) : (
          <ul className="space-y-1 font-mono text-small text-fg-2">
            {data.incidents.map((row) => (
              <li key={row.id}>
                {row.severity} · {row.engine} · {row.status} · {row.subject_id ?? "unattributed"}
              </li>
            ))}
          </ul>
        )}
      </SettingGroup>

      <SettingGroup id="security-quarantine" label="Quarantine" meta={String(data.quarantines.length)}>
        {data.quarantines.length === 0 ? (
          <p className="text-small text-fg-3">No active quarantine. Release stays Root-only when one exists.</p>
        ) : (
          <ul className="space-y-2 font-mono text-small text-fg-2">
            {data.quarantines.map((row) => (
              <li key={row.user_id} className="flex flex-wrap items-center gap-2">
                <span>
                  {row.user_id} · {row.status} · {row.prior_role_ids.length} prior roles
                </span>
                {isRoot ? (
                  <button
                    type="button"
                    className="border border-line-subtle px-2 py-1 text-fg-1"
                    onClick={() =>
                      void api.releaseQuarantine(guildId, row.user_id).catch(() =>
                        toast.error("Release stays locked"),
                      )
                    }
                  >
                    Release
                  </button>
                ) : null}
              </li>
            ))}
          </ul>
        )}
      </SettingGroup>

      {isRoot ? (
        <SaveBar
          dirty={dirty}
          saving={saving}
          error={null}
          onSave={() => void save()}
          onDiscard={() => {
            setHumanOn(data.human_mode !== "OFF");
            setBotOn(data.bot_mode !== "OFF");
          }}
        />
      ) : null}
    </SettingsInstrument>
  );
}
