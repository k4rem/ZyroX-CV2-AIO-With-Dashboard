"use client";

import React, { useState } from "react";
import { toast } from "sonner";
import { SaveBar } from "@/components/settings/save-bar";
import { SettingGroup } from "@/components/settings/setting-group";
import { SettingRow } from "@/components/settings/setting-row";
import { SettingsInstrument } from "@/components/settings/settings-instrument";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";
import { HealthBadge, HealthPanel } from "@/components/platform/health";
import type { ModuleHealth } from "@/lib/platformHealth";
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
  permission_health: ModuleHealth;
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
  analytics?: {
    total: number;
    by_severity: Record<string, number>;
    by_engine: Record<string, number>;
    by_action_class: Record<string, number>;
    by_outcome: Record<string, number>;
    series: Array<{ day: string; count: number }>;
    heatmap: Array<{ weekday: number; hour: number; count: number }> | null;
    event_stream: Array<{ id: string; event_type: string; actor_id: string | null; occurred_at: string }>;
  };
  center?: { dashboard_locked: boolean; phishing_action: string; trap_channel_ids: string[] };
};

export function SecurityPanel({
  initial,
  guildId,
  isRoot,
  channels = [],
}: {
  initial: SecuritySummary;
  guildId: string;
  isRoot: boolean;
  channels?: Array<{ id: string; name: string }>;
}) {
  const [data, setData] = useState(initial);
  const [humanOn, setHumanOn] = useState(initial.human_mode !== "OFF");
  const [botOn, setBotOn] = useState(initial.bot_mode !== "OFF");
  const [saving, setSaving] = useState(false);
  const [timeline, setTimeline] = useState<Array<{ kind: string; created_at: string; payload: Record<string, unknown> }>>([]);
  const [phishing, setPhishing] = useState(initial.center?.phishing_action ?? "delete_timeout");
  const [trapChannel, setTrapChannel] = useState(initial.center?.trap_channel_ids?.[0] ?? "");
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

      <SettingGroup id="security-analytics" label="Stored incidents">
        {!data.analytics || data.analytics.total === 0 ? (
          <p className="text-small text-fg-3">No incidents stored yet. Charts use saved incidents only.</p>
        ) : (
          <div className="grid gap-3 md:grid-cols-2">
            <ul className="text-small text-fg-2">
              {data.analytics.series.map((point) => (
                <li key={point.day} className="flex justify-between font-mono">
                  <span>{point.day}</span>
                  <span>{point.count}</span>
                </li>
              ))}
            </ul>
            <ul className="text-small text-fg-2">
              {Object.entries(data.analytics.by_severity).map(([name, count]) => (
                <li key={name}>Severity {name}: {count}</li>
              ))}
              {Object.entries(data.analytics.by_engine).map(([name, count]) => (
                <li key={name}>{name}: {count}</li>
              ))}
              {Object.entries(data.analytics.by_outcome).map(([name, count]) => (
                <li key={name}>Outcome {name}: {count}</li>
              ))}
            </ul>
          </div>
        )}
        {data.analytics?.heatmap ? (
          <p className="text-small text-fg-3">{data.analytics.heatmap.length} occupied hour cells.</p>
        ) : data.analytics && data.analytics.total > 0 ? (
          <p className="text-small text-fg-3">Not enough incident history for a heatmap.</p>
        ) : null}
      </SettingGroup>

      <SettingGroup id="security-stream" label="Security event stream">
        {(data.analytics?.event_stream ?? []).length === 0 ? (
          <p className="text-small text-fg-3">No stored moderation or bot events for this server.</p>
        ) : (
          <ul className="font-mono text-small text-fg-2">
            {data.analytics?.event_stream.map((row) => (
              <li key={row.id}>{row.occurred_at.slice(0, 16)} · {row.event_type} · {row.actor_id ?? "unknown"}</li>
            ))}
          </ul>
        )}
      </SettingGroup>

      <SettingGroup id="security-health" label="Health">
        <div className="mb-2 flex items-center gap-2">
          <HealthBadge status={data.permission_health.status} />
        </div>
        <HealthPanel health={data.permission_health} />
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
                <button
                  type="button"
                  className="text-left"
                  onClick={() =>
                    void api.getSecurityIncident(guildId, row.id).then((body) => setTimeline(body?.events ?? []))
                  }
                >
                  {row.severity} · {row.engine} · {row.status} · {row.subject_id ?? "unattributed"}
                </button>
              </li>
            ))}
          </ul>
        )}
      </SettingGroup>

      <SettingGroup id="security-timeline" label="Evidence timeline">
        {timeline.length === 0 ? (
          <p className="text-small text-fg-3">Select an incident to read its stored evidence.</p>
        ) : (
          <ul className="space-y-1 font-mono text-small text-fg-2">
            {timeline.map((row, index) => (
              <li key={`${row.created_at}-${index}`}>{row.created_at} · {row.kind}</li>
            ))}
          </ul>
        )}
      </SettingGroup>

      <SettingGroup id="security-config" label="Configuration">
        <SettingRow label="Phishing action" description="Recorded now. Punishment runs only if ENFORCE is later unlocked.">
          <Select
            value={phishing}
            options={[
              { value: "delete_only", label: "Delete only" },
              { value: "delete_timeout", label: "Delete and timeout" },
              { value: "kick", label: "Kick" },
              { value: "ban", label: "Ban" },
            ]}
            onValueChange={setPhishing}
          />
        </SettingRow>
        <SettingRow label="Bot trap channel" description="Untrusted bots that post here are recorded. Bans stay locked.">
          <Select
            value={trapChannel}
            options={channels.map((channel) => ({ value: channel.id, label: channel.name }))}
            placeholder="Select channel"
            onValueChange={setTrapChannel}
          />
        </SettingRow>
        <Button
          type="button"
          variant="secondary"
          onClick={() =>
            void api
              .updateSecurityCenter(guildId, {
                phishing_action: phishing,
                trap_channel_ids: trapChannel ? [trapChannel] : [],
              })
              .then(() => toast.success("Security configuration saved"))
              .catch(() => toast.error("Could not save security configuration"))
          }
        >
          Save configuration
        </Button>
        <SettingRow label="Dashboard lock" description="Non-root dashboard changes stop while this is on.">
          <Switch
            checked={!!data.center?.dashboard_locked}
            disabled={!isRoot}
            aria-label="Dashboard lock"
            onCheckedChange={(locked) =>
              void api
                .setDashboardLock(guildId, locked)
                .then(() => api.getSecurity(guildId))
                .then((next) => next && setData(next))
                .catch(() => toast.error("Only Root can change the dashboard lock"))
            }
          />
        </SettingRow>
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
