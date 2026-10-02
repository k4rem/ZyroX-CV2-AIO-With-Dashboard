"use client";

import { useEffect, useMemo, useState } from "react";
import { ActionResultView } from "@/components/platform/action-result";
import { DataTable } from "@/components/platform/data-table";
import { DetailsDrawer } from "@/components/platform/details-drawer";
import { HealthBadge, HealthPanel } from "@/components/platform/health";
import { SaveBar } from "@/components/settings/save-bar";
import { ChannelPicker, RolePicker, type ChannelOption, type RoleOption } from "@/components/discord/channel-picker";
import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import { api } from "@/lib/api";
import { actionSummary, durationLabel, exclusionSummary, thresholdSummary, type AutomodRule, type AutomodV2Config } from "@/lib/automodModel";
import type { PageSize } from "@/lib/pagination";
import type { ChannelCapabilities, HealthCheck, HealthStatus, ModuleHealth } from "@/lib/platformHealth";

type Runtime = {
  checks?: HealthCheck[];
  bot: { top_role_id: string; top_role_position: number; manage_roles: boolean } | null;
  channels?: Record<string, ChannelCapabilities>;
} | null;

const PERMS: Record<string, string> = {
  delete: "manage_messages",
  timeout: "moderate_members",
  kick: "kick_members",
  ban: "ban_members",
  channel: "send_messages",
  both: "send_messages",
};

function needed(config: AutomodV2Config): string[] {
  if (!config.enabled) return [];
  const ids = new Set<string>();
  for (const rule of config.rules) {
    if (!rule.enabled || rule.mode === "observe") continue;
    if (rule.message_action === "delete") ids.add("manage_messages");
    const member = PERMS[rule.member_action];
    if (member) ids.add(member);
    const notify = PERMS[rule.notify_action];
    if (notify) ids.add(notify);
  }
  return [...ids];
}

function draftHealth(config: AutomodV2Config, runtime: Runtime): ModuleHealth {
  const want = needed(config);
  const checks: HealthCheck[] = want.map((id) => {
    const found = runtime?.checks?.find((row) => row.id === id);
    return found || { id, label: id, ok: false, severity: "unavailable", fix_hint: "CLS is not available in this server.", scope: "guild" };
  });
  const failing = checks.filter((row) => !row.ok);
  const status: HealthStatus = failing.length === 0 ? "healthy" : failing.some((row) => row.severity === "error" || row.severity === "unavailable") ? "error" : "warning";
  return { status, checks: checks.length ? checks : config.health.checks };
}

export function AutomodWorkspace({
  guildId,
  tab,
  config,
  channels,
  roles,
  runtime,
}: {
  guildId: string;
  tab: "overview" | "rules" | "violations" | "strikes" | "settings";
  config: AutomodV2Config;
  channels: ChannelOption[];
  roles: RoleOption[];
  runtime: Runtime;
}) {
  const [draft, setDraft] = useState(config);
  const [saved, setSaved] = useState(config);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [advanced, setAdvanced] = useState(false);
  const [overview, setOverview] = useState<any>(null);
  const [violations, setViolations] = useState<any>(null);
  const [strikes, setStrikes] = useState<any[]>([]);
  const [tableError, setTableError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState<PageSize>(25);
  const [filters, setFilters] = useState({ rule: "", member: "", channel: "", action: "", result: "", since: "", until: "" });
  const [openId, setOpenId] = useState<string | null>(null);
  const [detail, setDetail] = useState<any>(null);
  const [sample, setSample] = useState("");
  const [sampleResult, setSampleResult] = useState<any[] | null>(null);
  const dirty = JSON.stringify(draft) !== JSON.stringify(saved);
  const health = useMemo(() => draftHealth(draft, runtime), [draft, runtime]);
  const rule = draft.rules.find((item) => item.id === selected) || null;

  useEffect(() => {
    if (tab !== "overview") return;
    api.getAutomodOverview(guildId).then(setOverview).catch((err) => setTableError(err.message));
  }, [guildId, tab, saved]);

  useEffect(() => {
    if (tab !== "violations") return;
    const params = new URLSearchParams({ page: String(page), page_size: String(pageSize) });
    for (const [key, value] of Object.entries(filters)) if (value) params.set(key, value);
    setLoading(true);
    api.getAutomodViolations(guildId, `?${params.toString()}`)
      .then((body) => {
        setViolations(body);
        setTableError(null);
      })
      .catch((err) => setTableError(err.message))
      .finally(() => setLoading(false));
  }, [guildId, tab, page, pageSize, filters]);

  useEffect(() => {
    if (tab !== "strikes") return;
    api.getAutomodStrikes(guildId).then((body) => setStrikes(body.rows)).catch((err) => setTableError(err.message));
  }, [guildId, tab]);

  function patchRule(id: string, patch: Partial<AutomodRule>) {
    setDraft((current) => ({
      ...current,
      preset: "custom",
      rules: current.rules.map((item) => (item.id === id ? { ...item, ...patch, trigger: patch.trigger || item.trigger, scope: patch.scope || item.scope } : item)),
    }));
  }

  async function onSave() {
    setSaving(true);
    setError(null);
    try {
      const next = await api.saveAutomodV2(guildId, draft);
      setDraft(next);
      setSaved(next);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Automod could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  async function applyPreset(preset: "relaxed" | "balanced" | "strict") {
    const body = await api.getAutomodPreset(guildId, preset);
    setDraft((current) => ({ ...current, preset, rules: body.rules.map((rule) => ({ ...rule, last_triggered_at: current.rules.find((item) => item.id === rule.id)?.last_triggered_at || null })) }));
  }

  return (
    <div className="space-y-4 pb-20">
      <PageHeader title="Automod" description="CLS checks each message against this server's rules, then records what happened." />
      <div className="flex flex-wrap items-center gap-2">
        <HealthBadge status={health.status} />
        <span className="rounded-xs border border-line px-1.5 py-0.5 text-[11px] text-fg-2">{saved.native?.label || "CLS"}</span>
        {saved.migrated ? <span className="text-caption text-fg-3">Migrated from the previous Automod config</span> : null}
      </div>
      {health.checks.some((row) => !row.ok) ? <HealthPanel health={health} /> : null}
      <ul className="space-y-1 text-caption text-fg-3">
        {(saved.health?.notes || []).slice(0, 3).map((note) => <li key={note}>{note}</li>)}
      </ul>

      {tab === "overview" ? (
        <Overview overview={overview} onTest={async () => setSampleResult((await api.testAutomodMessage(guildId, sample)).matches)} sample={sample} setSample={setSample} sampleResult={sampleResult} />
      ) : null}

      {tab === "rules" ? (
        <section className="space-y-3">
          <div className="flex flex-wrap gap-2">
            {(["relaxed", "balanced", "strict"] as const).map((preset) => (
              <Button key={preset} type="button" variant={draft.preset === preset ? "default" : "secondary"} onClick={() => applyPreset(preset)}>
                {preset[0].toUpperCase() + preset.slice(1)}
              </Button>
            ))}
            <span className="self-center text-caption text-fg-3">{draft.preset === "custom" ? "Custom" : "Preset values are shown on each rule."}</span>
          </div>
          <div className="border border-line">
            {draft.rules.map((item) => (
              <div key={item.id} className="grid grid-cols-1 gap-2 border-b border-line px-3 py-2 last:border-b-0 sm:grid-cols-[1fr_auto_auto] sm:items-center">
                <div>
                  <p className="text-small font-medium text-fg-1">{item.name}</p>
                  <p className="text-caption text-fg-3">
                    {thresholdSummary(item)} · {actionSummary(item)} · {exclusionSummary(item)} exclusions
                    {item.mode === "observe" ? " · Observe" : ""}
                  </p>
                </div>
                <Button type="button" variant="secondary" onClick={() => { setSelected(item.id); setAdvanced(false); }}>Configure</Button>
                <Switch checked={item.enabled} onCheckedChange={(enabled) => patchRule(item.id, { enabled })} aria-label={`${item.name} enabled`} />
              </div>
            ))}
          </div>
          {rule ? <RuleEditor rule={rule} advanced={advanced} setAdvanced={setAdvanced} channels={channels} roles={roles} runtime={runtime} onChange={(patch) => patchRule(rule.id, patch)} /> : null}
        </section>
      ) : null}

      {tab === "violations" ? (
        <Violations
          body={violations}
          loading={loading}
          error={tableError}
          page={page}
          pageSize={pageSize}
          filters={filters}
          onFilters={(next) => { setFilters(next); setPage(1); }}
          onPage={setPage}
          onPageSize={(size) => { setPageSize(size); setPage(1); }}
          onRetry={() => setPage(page)}
          onOpen={async (id) => {
            setOpenId(id);
            setDetail(await api.getAutomodViolation(guildId, id));
          }}
        />
      ) : null}

      {tab === "strikes" ? (
        <DataTable
          rows={strikes}
          columns={[
            { key: "member", header: "Member", cell: (row: any) => row.member_id },
            { key: "rule", header: "Rule", cell: (row: any) => row.rule_name },
            { key: "points", header: "Points", cell: (row: any) => row.points },
            { key: "source", header: "Source", cell: (row: any) => row.source },
            { key: "expires", header: "Expires", cell: (row: any) => row.expires_at },
          ]}
          getRowId={(row: any) => row.id}
          page={1}
          pages={1}
          pageSize={25}
          total={strikes.length}
          error={tableError}
          onPageChange={() => undefined}
          onPageSizeChange={() => undefined}
          emptyTitle="No strikes"
          emptyDescription="Warnings and rule points appear here after a real violation or a manual warn."
        />
      ) : null}

      {tab === "settings" ? (
        <Settings draft={draft} setDraft={setDraft} channels={channels} roles={roles} runtime={runtime} />
      ) : null}

      <DetailsDrawer
        open={Boolean(openId)}
        onOpenChange={(open) => { if (!open) { setOpenId(null); setDetail(null); } }}
        title={detail?.rule_name || "Violation"}
        summary={detail ? <ViolationSummary guildId={guildId} detail={detail} onChange={setDetail} onConfig={(next) => { setDraft(next); setSaved(next); }} /> : null}
        evidence={detail ? <p className="text-small text-fg-2">{detail.excerpt || "No excerpt stored."}</p> : null}
        ids={detail ? { violation_id: detail.id, member_id: detail.member_id, channel_id: detail.channel_id || "", log_event_id: detail.log_event_id || "" } : undefined}
        raw={detail}
      />
      <SaveBar dirty={dirty} saving={saving} error={error} onSave={onSave} onDiscard={() => { setDraft(saved); setError(null); }} />
    </div>
  );
}

function Overview({ overview, sample, setSample, sampleResult, onTest }: any) {
  if (!overview) return <p className="text-small text-fg-3">Loading Automod activity.</p>;
  const cards = [
    ["Status", overview.enabled ? "On" : "Off"],
    ["Enforcing rules", String(overview.enabled_rules)],
    ["Violations today", String(overview.violations_today)],
    ["Actions taken", String(overview.actions_taken)],
    ["Failed actions", String(overview.failed_actions)],
  ];
  return (
    <section className="space-y-3">
      <div className="grid grid-cols-2 gap-2 md:grid-cols-5">
        {cards.map(([label, value]) => (
          <article key={label} className="border border-line px-3 py-2">
            <p className="text-caption text-fg-3">{label}</p>
            <p className="text-section text-fg-1">{value}</p>
          </article>
        ))}
      </div>
      {overview.recent?.length ? (
        <ul className="divide-y divide-line border border-line">
          {overview.recent.map((row: any) => (
            <li key={row.id} className="px-3 py-2 text-small">
              <span className="text-fg-1">{row.rule_name}</span>
              <span className="text-fg-3"> · {row.summary} · {row.result_status}</span>
            </li>
          ))}
        </ul>
      ) : (
        <p className="border border-line px-3 py-6 text-small text-fg-3">No violations yet. Counts stay at zero until a message matches a rule.</p>
      )}
      <form className="flex flex-col gap-2 border border-line p-3 sm:flex-row" onSubmit={(event) => { event.preventDefault(); onTest(); }}>
        <Input value={sample} onChange={(event) => setSample(event.target.value)} placeholder="Test a message" aria-label="Test a message" />
        <Button type="submit">Test</Button>
      </form>
      {sampleResult ? (
        sampleResult.length ? (
          <ul className="space-y-2">
            {sampleResult.map((hit: any) => (
              <li key={hit.rule_id} className="border border-line px-3 py-2 text-small">
                <p className="text-fg-1">{hit.name} · {hit.summary}</p>
                <p className="text-fg-3">{(hit.would_run || []).map((item: any) => item.label).join(", ") || "No action"}{hit.mode === "observe" ? " · Observe, nothing is punished" : ""}</p>
              </li>
            ))}
          </ul>
        ) : <p className="text-small text-fg-3">No enabled rule matches that message.</p>
      ) : null}
    </section>
  );
}

function RuleEditor({ rule, advanced, setAdvanced, channels, roles, runtime, onChange }: {
  rule: AutomodRule;
  advanced: boolean;
  setAdvanced: (value: boolean) => void;
  channels: ChannelOption[];
  roles: RoleOption[];
  runtime: Runtime;
  onChange: (patch: Partial<AutomodRule>) => void;
}) {
  const trigger = rule.trigger as any;
  return (
    <section className="space-y-3 border border-line p-3">
      <header className="flex items-center justify-between gap-2">
        <h2 className="text-section text-fg-1">{rule.name}</h2>
        <Button type="button" variant="ghost" onClick={() => setAdvanced(!advanced)}>{advanced ? "Hide advanced" : "Advanced"}</Button>
      </header>
      <div className="grid gap-3 md:grid-cols-3">
        <label className="text-caption text-fg-3">Message
          <select className="mt-1 w-full border border-line bg-surface-1 px-2 py-1 text-small" value={rule.message_action} onChange={(event) => onChange({ message_action: event.target.value as AutomodRule["message_action"] })}>
            <option value="keep">Keep</option>
            <option value="delete">Delete</option>
          </select>
        </label>
        <label className="text-caption text-fg-3">Member
          <select className="mt-1 w-full border border-line bg-surface-1 px-2 py-1 text-small" value={rule.member_action} onChange={(event) => onChange({ member_action: event.target.value as AutomodRule["member_action"] })}>
            <option value="none">None</option>
            <option value="warn">Warn</option>
            <option value="timeout">Timeout</option>
            <option value="kick">Kick</option>
            <option value="ban">Ban</option>
          </select>
        </label>
        <label className="text-caption text-fg-3">Notify
          <select className="mt-1 w-full border border-line bg-surface-1 px-2 py-1 text-small" value={rule.notify_action} onChange={(event) => onChange({ notify_action: event.target.value as AutomodRule["notify_action"] })}>
            <option value="none">None</option>
            <option value="dm">DM</option>
            <option value="channel">Channel notice</option>
            <option value="both">DM + channel notice</option>
          </select>
        </label>
      </div>
      {rule.member_action === "timeout" ? (
        <label className="block text-caption text-fg-3">Timeout
          <Input className="mt-1" type="number" min={60} max={2419200} value={rule.timeout_seconds} onChange={(event) => onChange({ timeout_seconds: Number(event.target.value) })} />
          <span className="text-fg-3"> {durationLabel(rule.timeout_seconds)} · 60 seconds to 28 days</span>
        </label>
      ) : null}
      <SimpleTrigger rule={rule} trigger={trigger} onChange={onChange} />
      {advanced ? (
        <div className="space-y-3 border-t border-line pt-3">
          <label className="flex items-center gap-2 text-small text-fg-2">
            <Switch checked={rule.mode === "observe"} onCheckedChange={(on) => onChange({ mode: on ? "observe" : "enforce" })} />
            Observe only. Matches are stored and logged. Nothing is punished.
          </label>
          <label className="block text-caption text-fg-3">Strike points
            <Input className="mt-1" type="number" min={0} max={100} value={rule.points} onChange={(event) => onChange({ points: Number(event.target.value) })} />
          </label>
          <p className="text-caption text-fg-3">Explicit exclusions win over included channels.</p>
          <ChannelPicker channels={channels} value="" onChange={(id) => onChange({ scope: { ...rule.scope, exclude_channels: [...new Set([...rule.scope.exclude_channels, id])] } })} capabilities={runtime?.channels} required={["view_channel"]} intent="mutate" />
          <RolePicker roles={roles} value="" onChange={(id) => onChange({ scope: { ...rule.scope, exclude_roles: [...new Set([...rule.scope.exclude_roles, id])] } })} botPosition={runtime?.bot?.top_role_position} botRoleId={runtime?.bot?.top_role_id} manageRoles={runtime?.bot?.manage_roles} intent="mutate" allowEmpty />
          <p className="text-caption text-fg-3">Excluded channels: {rule.scope.exclude_channels.join(", ") || "none"} · Excluded roles: {rule.scope.exclude_roles.join(", ") || "none"}</p>
        </div>
      ) : null}
    </section>
  );
}

function SimpleTrigger({ rule, trigger, onChange }: { rule: AutomodRule; trigger: any; onChange: (patch: Partial<AutomodRule>) => void }) {
  const set = (next: Record<string, unknown>) => onChange({ trigger: { ...trigger, ...next } });
  if (rule.id === "flood" || rule.id === "duplicate") {
    return (
      <div className="grid gap-3 md:grid-cols-2">
        <Field label="Count" value={trigger.count} onChange={(count) => set({ count })} />
        <Field label="Seconds" value={trigger.window_seconds} onChange={(window_seconds) => set({ window_seconds })} />
      </div>
    );
  }
  if (rule.id === "caps") {
    return (
      <div className="grid gap-3 md:grid-cols-2">
        <Field label="Percent" value={trigger.percent} onChange={(percent) => set({ percent })} />
        <Field label="Minimum length" value={trigger.min_length} onChange={(min_length) => set({ min_length })} />
      </div>
    );
  }
  if (rule.id === "mentions" || rule.id === "emoji") return <Field label="Threshold" value={trigger.count} onChange={(count) => set({ count })} />;
  if (rule.id === "links") {
    return (
      <div className="space-y-2">
        <label className="text-caption text-fg-3">Mode
          <select className="mt-1 w-full border border-line bg-surface-1 px-2 py-1 text-small" value={trigger.mode} onChange={(event) => set({ mode: event.target.value })}>
            <option value="block">Block</option>
            <option value="allow">Allow, except the deny list</option>
          </select>
        </label>
        <ListField label="Allow domains" value={(trigger.allow || []).join("\n")} onChange={(allow) => set({ allow: allow.split("\n").map((item) => item.trim()).filter(Boolean) })} />
        <ListField label="Deny domains" value={(trigger.deny || []).join("\n")} onChange={(deny) => set({ deny: deny.split("\n").map((item) => item.trim()).filter(Boolean) })} />
      </div>
    );
  }
  if (rule.id === "bad_words" || rule.id === "keyword") {
    const key = rule.id === "bad_words" ? "terms" : "phrases";
    return (
      <div className="space-y-2">
        <label className="text-caption text-fg-3">Match
          <select className="mt-1 w-full border border-line bg-surface-1 px-2 py-1 text-small" value={trigger.mode} onChange={(event) => set({ mode: event.target.value })}>
            <option value="whole">Whole word</option>
            <option value="contains">Contains</option>
            <option value="wildcard">Wildcard</option>
          </select>
        </label>
        <ListField label={rule.id === "bad_words" ? "Words" : "Phrases"} value={(trigger[key] || []).join("\n")} onChange={(text) => set({ [key]: text.split("\n").map((item) => item.trim()).filter(Boolean) })} />
        {rule.id === "bad_words" ? <ListField label="Exceptions" value={(trigger.exceptions || []).join("\n")} onChange={(text) => set({ exceptions: text.split("\n").map((item) => item.trim()).filter(Boolean) })} /> : null}
      </div>
    );
  }
  if (rule.id === "attachments") {
    return (
      <label className="text-caption text-fg-3">Policy
        <select className="mt-1 w-full border border-line bg-surface-1 px-2 py-1 text-small" value={trigger.policy} onChange={(event) => set({ policy: event.target.value })}>
          <option value="allow">Allow</option>
          <option value="block">Block attachments</option>
          <option value="images_only">Images only</option>
          <option value="attachments_only">Attachments only</option>
          <option value="image_channel">Image-only channel</option>
        </select>
      </label>
    );
  }
  return null;
}

function Field({ label, value, onChange }: { label: string; value: number; onChange: (value: number) => void }) {
  return (
    <label className="text-caption text-fg-3">{label}
      <Input className="mt-1" type="number" value={value} onChange={(event) => onChange(Number(event.target.value))} />
    </label>
  );
}

function ListField({ label, value, onChange }: { label: string; value: string; onChange: (value: string) => void }) {
  return (
    <label className="block text-caption text-fg-3">{label}
      <Textarea className="mt-1" value={value} onChange={(event) => onChange(event.target.value)} />
    </label>
  );
}

function Settings({ draft, setDraft, channels, roles, runtime }: { draft: AutomodV2Config; setDraft: (value: AutomodV2Config) => void; channels: ChannelOption[]; roles: RoleOption[]; runtime: Runtime }) {
  return (
    <section className="space-y-4">
      <label className="flex items-center justify-between border border-line px-3 py-2 text-small">
        Automod enabled
        <Switch checked={draft.enabled} onCheckedChange={(enabled) => setDraft({ ...draft, enabled })} />
      </label>
      <div>
        <h2 className="text-section text-fg-1">Staff immunity</h2>
        <p className="mb-2 text-caption text-fg-3">These roles are exempt. The exemption is shown here and is never implied.</p>
        <RolePicker roles={roles} value="" onChange={(id) => setDraft({ ...draft, preset: "custom", exclusions: { ...draft.exclusions, staff_roles: [...new Set([...draft.exclusions.staff_roles, id])] } })} botPosition={runtime?.bot?.top_role_position} botRoleId={runtime?.bot?.top_role_id} manageRoles={runtime?.bot?.manage_roles} intent="mutate" allowEmpty />
        <p className="mt-1 text-caption text-fg-2">{draft.exclusions.staff_roles.map((id) => roles.find((role) => role.id === id)?.name || id).join(", ") || "No staff role is exempt."}</p>
      </div>
      <div>
        <h2 className="text-section text-fg-1">Global exclusions</h2>
        <p className="mb-2 text-caption text-fg-3">A global exclusion wins over every rule, including an include list.</p>
        <ChannelPicker channels={channels} value="" onChange={(id) => setDraft({ ...draft, preset: "custom", exclusions: { ...draft.exclusions, channels: [...new Set([...draft.exclusions.channels, id])] } })} capabilities={runtime?.channels} required={["view_channel", "send_messages"]} intent="mutate" />
        <p className="mt-1 text-caption text-fg-3">Channels: {draft.exclusions.channels.length} · Roles: {draft.exclusions.roles.length} · Members: {draft.exclusions.members.length}</p>
      </div>
      <div className="space-y-2">
        <h2 className="text-section text-fg-1">Escalation</h2>
        <p className="text-caption text-fg-3">The highest matching threshold runs once. A lower match in the same evaluation does not also run.</p>
        {draft.escalations.map((row, index) => (
          <div key={`${row.points}-${index}`} className="grid grid-cols-2 gap-2 border border-line p-2 md:grid-cols-4">
            <Field label="Points" value={row.points} onChange={(points) => {
              const escalations = draft.escalations.map((item, itemIndex) => itemIndex === index ? { ...item, points } : item);
              setDraft({ ...draft, preset: "custom", escalations });
            }} />
            <Field label="Window seconds" value={row.window_seconds} onChange={(window_seconds) => {
              const escalations = draft.escalations.map((item, itemIndex) => itemIndex === index ? { ...item, window_seconds } : item);
              setDraft({ ...draft, preset: "custom", escalations });
            }} />
            <p className="self-end text-small text-fg-2">{row.action}{row.duration_seconds ? ` ${durationLabel(row.duration_seconds)}` : ""}</p>
          </div>
        ))}
      </div>
      {draft.migration_notes?.length ? (
        <ul className="space-y-1 text-caption text-fg-3">{draft.migration_notes.map((note) => <li key={note}>{note}</li>)}</ul>
      ) : null}
    </section>
  );
}

function Violations(props: {
  body: any;
  loading: boolean;
  error: string | null;
  page: number;
  pageSize: PageSize;
  filters: { rule: string; member: string; channel: string; action: string; result: string; since: string; until: string };
  onFilters: (next: { rule: string; member: string; channel: string; action: string; result: string; since: string; until: string }) => void;
  onPage: (page: number) => void;
  onPageSize: (size: PageSize) => void;
  onRetry: () => void;
  onOpen: (id: string) => void;
}) {
  const rows = props.body?.rows || [];
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 gap-2 md:grid-cols-3">
        {(["rule", "member", "channel", "action", "result"] as const).map((key) => (
          <Input key={key} aria-label={key} placeholder={key} value={props.filters[key]} onChange={(event) => props.onFilters({ ...props.filters, [key]: event.target.value })} />
        ))}
      </div>
      <DataTable
        rows={rows}
        columns={[
          { key: "member", header: "Member", cell: (row: any) => row.member_id },
          { key: "channel", header: "Channel", cell: (row: any) => row.channel_id || "—" },
          { key: "rule", header: "Rule", cell: (row: any) => row.rule_name },
          { key: "summary", header: "Summary", cell: (row: any) => row.summary },
          { key: "result", header: "Result", cell: (row: any) => row.result_status },
          { key: "time", header: "Time", cell: (row: any) => row.occurred_at },
        ]}
        getRowId={(row: any) => row.id}
        page={props.body?.page || props.page}
        pages={props.body?.pages || 1}
        pageSize={props.pageSize}
        total={props.body?.total || 0}
        loading={props.loading}
        error={props.error}
        onRetry={props.onRetry}
        onPageChange={props.onPage}
        onPageSizeChange={props.onPageSize}
        onSelect={props.onOpen}
        emptyTitle="No violations"
        emptyDescription="Matches from enforcing and observe rules are listed here."
      />
    </div>
  );
}

function ViolationSummary({ guildId, detail, onChange, onConfig }: { guildId: string; detail: any; onChange: (value: any) => void; onConfig: (value: AutomodV2Config) => void }) {
  const [follow, setFollow] = useState(detail.followups?.[0]?.kind || "");
  const [value, setValue] = useState("");
  const [note, setNote] = useState<string | null>(null);
  return (
    <div className="space-y-3">
      <p className="text-small text-fg-1">{detail.summary}</p>
      <p className="text-caption text-fg-3">Engine {detail.engine} · {detail.false_positive ? "Marked false positive" : "Open"}</p>
      <div className="space-y-2">
        {(detail.actions || []).map((action: any, index: number) => (
          <ActionResultView key={`${action.kind}-${index}`} result={{ outcome: action.outcome, reason: action.reason, context: action.context || action.label, discordError: action.discord_error, at: detail.occurred_at }} />
        ))}
      </div>
      {detail.strike ? <p className="text-caption text-fg-3">Strike {detail.strike.points || ""} {detail.strike.strike_id || ""}</p> : null}
      {detail.log_event_id ? <p className="text-caption text-fg-3">Logging event {detail.log_event_id}</p> : null}
      <Button type="button" variant="secondary" onClick={async () => onChange(await api.markAutomodFalsePositive(guildId, detail.id))}>Mark false positive</Button>
      <div className="space-y-2 border-t border-line pt-2">
        <p className="text-caption text-fg-3">A follow-up changes policy only after you confirm it.</p>
        <select className="w-full border border-line bg-surface-1 px-2 py-1 text-small" value={follow} onChange={(event) => setFollow(event.target.value)}>
          {(detail.followups || []).map((item: any) => <option key={item.kind} value={item.kind}>{item.label}</option>)}
        </select>
        <Input value={value} onChange={(event) => setValue(event.target.value)} placeholder="Channel, role, word, or domain" aria-label="Follow-up value" />
        <Button type="button" onClick={async () => {
          try {
            onConfig(await api.applyAutomodFollowup(guildId, detail.id, { confirm: true, kind: follow, value }));
            setNote("Saved.");
          } catch (err) {
            setNote(err instanceof Error ? err.message : "Could not save the follow-up.");
          }
        }}>Confirm follow-up</Button>
        {note ? <p className="text-caption text-fg-3">{note}</p> : null}
      </div>
    </div>
  );
}
