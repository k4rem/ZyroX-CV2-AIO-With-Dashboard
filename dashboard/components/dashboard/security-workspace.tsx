"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { Lock } from "lucide-react";
import { ActionResultView } from "@/components/platform/action-result";
import { ActivitySentence } from "@/components/platform/activity-sentence";
import { DataTable } from "@/components/platform/data-table";
import { DetailsDrawer } from "@/components/platform/details-drawer";
import { HealthBadge, HealthPanel } from "@/components/platform/health";
import { SaveBar } from "@/components/settings/save-bar";
import { ChannelPicker, type ChannelOption } from "@/components/discord/channel-picker";
import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ErrorState } from "@/components/ui/state";
import { api } from "@/lib/api";
import type { ActionResult } from "@/lib/actionResult";
import type { PageSize } from "@/lib/pagination";
import type { ModuleHealth } from "@/lib/platformHealth";
import { cn } from "@/lib/utils";

export type SecurityTab = "overview" | "incidents" | "detectors" | "trust" | "traps" | "quarantine" | "settings";

const TABS: Array<{ id: SecurityTab; path: string; label: string }> = [
  { id: "overview", path: "", label: "Overview" },
  { id: "incidents", path: "/incidents", label: "Incidents" },
  { id: "detectors", path: "/detectors", label: "Detectors" },
  { id: "trust", path: "/trust", label: "Trust" },
  { id: "traps", path: "/traps", label: "Traps & Phishing" },
  { id: "quarantine", path: "/quarantine", label: "Quarantine & Recovery" },
  { id: "settings", path: "/settings", label: "Settings" },
];

function resultOf(row: { outcome?: string; reason?: string; discord_error?: string; context?: string }): ActionResult {
  const outcome = row.outcome === "succeeded" || row.outcome === "failed" || row.outcome === "skipped" ? row.outcome : "failed";
  return { outcome, reason: row.reason || "No result recorded", discordError: row.discord_error, context: row.context };
}

export function SecurityWorkspace({
  guildId,
  tab,
  initial,
  isRoot,
  channels,
}: {
  guildId: string;
  tab: SecurityTab;
  initial: any;
  isRoot: boolean;
  channels: ChannelOption[];
}) {
  const router = useRouter();
  const [data, setData] = useState(initial);
  const [error, setError] = useState<string | null>(null);
  const health = (data.permission_health || { status: "unavailable", checks: [] }) as ModuleHealth;
  const base = `/dashboard/guild/${guildId}/antinuke`;

  async function reload() {
    try {
      setData(await api.getSecurity(guildId));
      setError(null);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Security state could not be loaded.");
    }
  }

  return (
    <div className="space-y-4 pb-20">
      <PageHeader title="Security Center" description="What CLS is watching, what it recorded, and what it will not do while enforcement is locked." />
      <nav aria-label="Security" className="flex gap-1 overflow-x-auto border-b border-line">
        {TABS.map((item) => (
          <Link
            key={item.id}
            href={`${base}${item.path}`}
            className={cn(
              "shrink-0 border-b-2 px-3 py-2 text-small",
              tab === item.id ? "border-brand-400 text-fg-1" : "border-transparent text-fg-3 hover:text-fg-1",
            )}
          >
            {item.label}
          </Link>
        ))}
      </nav>
      {error ? <ErrorState title="Security state could not be loaded" description={error} actions={<Button type="button" onClick={() => void reload()}>Retry</Button>} /> : null}
      {tab === "overview" ? <Overview data={data} health={health} /> : null}
      {tab === "incidents" ? <Incidents guildId={guildId} /> : null}
      {tab === "detectors" ? <Detectors data={data} /> : null}
      {tab === "trust" ? <Trust guildId={guildId} data={data} isRoot={isRoot} onChange={reload} /> : null}
      {tab === "traps" ? <Traps guildId={guildId} data={data} channels={channels} onChange={reload} /> : null}
      {tab === "quarantine" ? <Quarantine guildId={guildId} data={data} isRoot={isRoot} onChange={() => router.refresh()} /> : null}
      {tab === "settings" ? <Settings guildId={guildId} data={data} isRoot={isRoot} onChange={reload} /> : null}
    </div>
  );
}

function Overview({ data, health }: { data: any; health: ModuleHealth }) {
  const behavior = data.behavior || { will: [], will_not: [] };
  const signal = data.join_signal;
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <span className="border border-line px-2 py-1 text-small text-fg-1">Posture: {data.posture || "Normal"}</span>
        <HealthBadge status={health.status} />
        <span className={cn("inline-flex items-center gap-1 border px-2 py-1 text-small", data.enforce_locked ? "border-locked/40 bg-locked/10 text-locked" : "border-line text-fg-1")}>
          {data.enforce_locked ? <Lock className="size-3" aria-hidden="true" /> : null}
          ENFORCE {data.enforce_locked ? "locked" : "available"}
        </span>
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        <Fact label="Human protection" value={data.effective_human_mode === "OFF" ? "Off" : "Detect, record, alert"} />
        <Fact label="Bot protection" value={data.effective_bot_mode === "OFF" ? "Off" : "Detect, record, alert"} />
        <Fact label="Open incidents" value={String((data.incidents || []).filter((row: any) => row.status === "ACTIVE").length)} />
      </div>
      <section className="border border-line bg-surface-1 p-3">
        <h2 className="text-section text-fg-1">What CLS will do right now</h2>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <div>
            <p className="text-caption text-fg-3">CLS will</p>
            <ul className="mt-1 space-y-1 text-small text-fg-1">{(behavior.will || []).map((item: string) => <li key={item}>{item}</li>)}</ul>
          </div>
          <div>
            <p className="text-caption text-fg-3">CLS will not</p>
            <ul className="mt-1 space-y-1 text-small text-fg-1">{(behavior.will_not || []).map((item: string) => <li key={item}>{item}</li>)}</ul>
          </div>
        </div>
      </section>
      <HealthPanel health={health} />
      <div className="grid gap-3 md:grid-cols-3">
        <Fact label="Alerts" value={data.ops?.destination_label || "Not configured"} detail={data.ops?.last ? `Last ${data.ops.last.status}` : "No delivery recorded"} />
        <Fact label="Recovery snapshot" value={data.recovery?.latest_snapshot_at ? "Snapshot available" : "No snapshot"} detail={data.recovery?.restore_locked ? "Restore stays locked" : undefined} />
        <Fact label="Joins" value={signal ? `${signal.recent_joins} in ${signal.window_minutes} minutes` : "Unavailable"} detail={signal?.explanation} />
      </div>
      {data.maintenance ? <p className="border border-warn/30 bg-warn/10 px-3 py-2 text-small text-fg-1">Maintenance is active until {data.maintenance.ends_at}. Protection stays in observe. Reason: {data.maintenance.reason}</p> : null}
    </div>
  );
}

function Fact({ label, value, detail }: { label: string; value: string; detail?: string }) {
  return (
    <article className="border border-line bg-surface-1 px-3 py-2">
      <p className="text-caption text-fg-3">{label}</p>
      <p className="text-small text-fg-1">{value}</p>
      {detail ? <p className="text-caption text-fg-3">{detail}</p> : null}
    </article>
  );
}

function Incidents({ guildId }: { guildId: string }) {
  const [rows, setRows] = useState<any[]>([]);
  const [page, setPage] = useState(1);
  const [pages, setPages] = useState(1);
  const [total, setTotal] = useState(0);
  const [pageSize, setPageSize] = useState<PageSize>(25);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({ status: "", severity: "", detector: "", actor: "", target: "", confidence: "", start: "", end: "" });
  const [openId, setOpenId] = useState<string | null>(null);
  const [detail, setDetail] = useState<any>(null);
  const [note, setNote] = useState("");
  const [pending, setPending] = useState<string | null>(null);

  function load(nextPage = page, nextSize = pageSize) {
    const params = new URLSearchParams({ page: String(nextPage), page_size: String(nextSize) });
    for (const [key, value] of Object.entries(filters)) if (value) params.set(key, value);
    setLoading(true);
    api.getSecurityIncidents(guildId, `?${params.toString()}`)
      .then((body) => {
        setRows(body.rows || []);
        setPages(body.pages || 1);
        setTotal(body.total || 0);
        setError(null);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Incidents could not be loaded."))
      .finally(() => setLoading(false));
  }

  useEffect(() => {
    load(1, pageSize);
    setPage(1);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [guildId, pageSize, filters]);

  async function open(id: string) {
    setOpenId(id);
    setDetail(null);
    try {
      setDetail(await api.getSecurityIncident(guildId, id));
    } catch (err) {
      setDetail({ error: err instanceof Error ? err.message : "Incident could not be loaded." });
    }
  }

  async function close(closure: "RESOLVED" | "FALSE_POSITIVE") {
    if (!openId || pending !== closure) {
      setPending(closure);
      return;
    }
    const body = await api.closeSecurityIncident(guildId, openId, { closure, note });
    setDetail(body);
    setPending(null);
    load();
  }

  return (
    <div className="space-y-3">
      <div className="grid gap-2 md:grid-cols-4">
        {(["status", "severity", "detector", "actor", "target", "confidence", "start", "end"] as const).map((key) => (
          <Input key={key} aria-label={key} placeholder={key} value={filters[key]} onChange={(event) => setFilters((current) => ({ ...current, [key]: event.target.value }))} />
        ))}
      </div>
      <DataTable
        rows={rows}
        page={page}
        pages={pages}
        pageSize={pageSize}
        total={total}
        loading={loading}
        error={error}
        onRetry={() => load()}
        onPageChange={(next) => {
          setPage(next);
          load(next);
        }}
        onPageSizeChange={setPageSize}
        selectedId={openId}
        onSelect={(id) => void open(id)}
        getRowId={(row) => row.id}
        emptyTitle="No incidents"
        emptyDescription="CLS has not opened an incident for this filter."
        columns={[
          { key: "title", header: "Incident", cell: (row) => <span><span className="block text-fg-1">{row.title}</span><span className="text-caption text-fg-3">{row.subtitle}</span></span> },
          { key: "severity", header: "Severity", cell: (row) => row.severity_label },
          { key: "status", header: "Status", cell: (row) => row.status_label },
          { key: "actor", header: "Actor", cell: (row) => row.actor_id || "Unknown" },
          { key: "confidence", header: "Confidence", cell: (row) => row.confidence_label },
          { key: "time", header: "Time", cell: (row) => row.opened_at || "" },
          { key: "detector", header: "Detector", cell: (row) => row.detector },
        ]}
      />
      <DetailsDrawer
        open={Boolean(openId)}
        onOpenChange={(open) => {
          if (!open) setOpenId(null);
        }}
        title={detail?.title || "Incident"}
        ids={detail?.developer ? { incident: detail.developer.incident_id, engine: detail.developer.engine, detector: detail.developer.detector_id, actor: detail.developer.subject_id || "" } : undefined}
        raw={detail?.developer}
        summary={detail?.error ? <ErrorState title="Incident could not be loaded" description={detail.error} actions={<Button type="button" onClick={() => openId && void open(openId)}>Retry</Button>} /> : (
          <div className="space-y-3">
            <p className="text-fg-1">{detail?.summary}</p>
            <p>Actor {detail?.actor_id || "Unknown"} · {detail?.severity_label} · {detail?.status_label}</p>
            <p>Confidence: {detail?.confidence_label} · Detector: {detail?.detector}</p>
            <p className="text-caption text-fg-3">{detail?.opened_at}</p>
            <div className="space-y-2">
              {(detail?.timeline || []).map((row: any, index: number) => (
                <ActivitySentence key={index} event={{ actor: "CLS", verb: "recorded", object: row.sentence, at: row.at, form: "event" }} />
              ))}
            </div>
            <div className="space-y-2">
              {(detail?.response?.did || []).map((row: any, index: number) => <ActionResultView key={index} result={resultOf(row)} />)}
            </div>
            {detail?.response?.enforce_locked ? (
              <div className="border border-locked/40 bg-locked/10 p-2 text-locked">
                <p className="inline-flex items-center gap-1"><Lock className="size-3" aria-hidden="true" /> Locked until ENFORCE is available</p>
                <ul className="mt-1 text-fg-2">{(detail.response.would_enforce || []).map((item: string) => <li key={item}>{item}</li>)}</ul>
              </div>
            ) : null}
            {detail?.status === "ACTIVE" ? (
              <div className="flex flex-wrap gap-2">
                <Button type="button" onClick={() => void close("RESOLVED")}>{pending === "RESOLVED" ? "Confirm resolve" : "Resolve"}</Button>
                <Button type="button" variant="secondary" onClick={() => void close("RESOLVED")}>{pending === "RESOLVED" ? "Confirm resolve with note" : "Resolve with note"}</Button>
                <Button type="button" variant="secondary" onClick={() => void close("FALSE_POSITIVE")}>{pending === "FALSE_POSITIVE" ? "Confirm false positive" : "Mark false positive"}</Button>
              </div>
            ) : null}
            {pending ? <Input aria-label="Note" placeholder="Note" value={note} onChange={(event) => setNote(event.target.value)} /> : null}
            {detail?.offer_trust ? <p>False positive is recorded. Scoped trust is a separate Root action on the Trust page. CLS did not change trust.</p> : null}
          </div>
        )}
        evidence={<div className="space-y-2">{(detail?.evidence || []).map((row: any, index: number) => <p key={index}>{row.detector}: {row.summary} · {row.confidence_label}</p>)}</div>}
      />
    </div>
  );
}

function Detectors({ data }: { data: any }) {
  return (
    <div className="space-y-4">
      {(data.detectors || []).map((group: any) => (
        <section key={group.name}>
          <h2 className="mb-2 text-section text-fg-1">{group.name}</h2>
          <div className="grid gap-2 md:grid-cols-2">
            {(group.detectors || []).map((row: any) => (
              <article key={row.id} className="border border-line bg-surface-1 p-3">
                <h3 className="text-small text-fg-1">{row.title}</h3>
                <p className="text-caption text-fg-3">{row.description}</p>
                <p className="mt-2 text-caption text-fg-2">{row.threshold} in {row.window_s}s · {row.mode} · {row.response}</p>
                <p className="text-caption text-fg-3">Last triggered {row.last_triggered_at || "never"} · {row.triggers_30d} in 30 days</p>
                {row.provisional ? <p className="mt-2 inline-flex border border-warn/40 bg-warn/10 px-1.5 py-0.5 text-caption text-warn">{row.provisional_label}. {row.provisional_detail}</p> : null}
              </article>
            ))}
          </div>
        </section>
      ))}
    </div>
  );
}

function Trust({ guildId, data, isRoot, onChange }: { guildId: string; data: any; isRoot: boolean; onChange: () => Promise<void> }) {
  const [subject, setSubject] = useState("");
  const [scope, setScope] = useState("*");
  const [minutes, setMinutes] = useState("");
  const [reason, setReason] = useState("");
  const [kind, setKind] = useState("human");
  const [pending, setPending] = useState(false);
  const [revokeId, setRevokeId] = useState<string | null>(null);
  const [result, setResult] = useState<string | null>(null);
  const actors: any[] = data.trusted_actors || [];
  const option = (data.scope_options || []).find((item: any) => item.id === scope);

  async function grant() {
    if (!pending) {
      setPending(true);
      return;
    }
    const expires = minutes ? new Date(Date.now() + Number(minutes) * 60000).toISOString() : null;
    await api.grantSecurityTrust(guildId, {
      subject_id: subject,
      kind,
      scopes: option?.scopes || [scope],
      expires_at: expires,
      reason,
    });
    setPending(false);
    setResult("Trust granted.");
    await onChange();
  }

  return (
    <div className="space-y-4">
      <p className="text-small text-fg-2">Guild Owner and CLS Root are trusted by ownership. They are not rows in this list. Grants below are Trusted Admin or Trusted Bot, and only Root can change them.</p>
      <DataTable
        rows={actors}
        page={1}
        pages={1}
        pageSize={25}
        total={actors.length}
        onPageChange={() => undefined}
        onPageSizeChange={() => undefined}
        getRowId={(row) => row.subject_id}
        emptyTitle="No trust grants"
        emptyDescription="Owner and Root access still applies. Extra trust has not been granted."
        columns={[
          { key: "actor", header: "Actor", cell: (row) => row.subject_id },
          { key: "tier", header: "Tier", cell: (row) => row.tier },
          { key: "scope", header: "Scope", cell: (row) => row.scope_label },
          { key: "by", header: "Granted by", cell: (row) => row.granted_by },
          { key: "at", header: "Granted at", cell: (row) => row.granted_at || "" },
          { key: "reason", header: "Reason", cell: (row) => row.reason || "Recorded in the audit log" },
          { key: "expiry", header: "Expiry", cell: (row) => row.expires_at || "None" },
          { key: "action", header: "", cell: (row) => isRoot ? <Button type="button" variant="secondary" onClick={() => { if (revokeId !== row.subject_id) { setRevokeId(row.subject_id); return; } void api.revokeSecurityTrust(guildId, row.subject_id).then(() => { setRevokeId(null); return onChange(); }); }}>{revokeId === row.subject_id ? "Confirm revoke" : "Revoke"}</Button> : <span className="text-locked">Root only</span> },
        ]}
      />
      {isRoot ? (
        <div className="grid gap-2 border border-line p-3 md:grid-cols-2">
          <Input aria-label="Actor" placeholder="Actor id" value={subject} onChange={(event) => setSubject(event.target.value)} />
          <select aria-label="Kind" className="h-9 border border-line bg-surface-1 px-2 text-small" value={kind} onChange={(event) => setKind(event.target.value)}>
            <option value="human">Trusted Admin</option>
            <option value="bot">Trusted Bot</option>
          </select>
          <select aria-label="Scope" className="h-9 border border-line bg-surface-1 px-2 text-small" value={scope} onChange={(event) => setScope(event.target.value)}>
            {(data.scope_options || []).map((item: any) => <option key={item.id} value={item.id}>{item.title}</option>)}
          </select>
          <Input aria-label="Minutes" placeholder="Minutes, blank for no expiry" value={minutes} onChange={(event) => setMinutes(event.target.value)} />
          <Input aria-label="Reason" placeholder="Reason" value={reason} onChange={(event) => setReason(event.target.value)} />
          <Button type="button" onClick={() => void grant()}>{pending ? "Confirm grant" : "Grant trust"}</Button>
          {result ? <p className="text-small text-fg-2">{result}</p> : null}
        </div>
      ) : <p className="border border-locked/40 bg-locked/10 px-3 py-2 text-small text-locked">Grant and revoke stay with CLS Root.</p>}
    </div>
  );
}

function Traps({ guildId, data, channels, onChange }: { guildId: string; data: any; channels: ChannelOption[]; onChange: () => Promise<void> }) {
  const center = data.center || {};
  const [honeypot, setHoneypot] = useState(center.honeypot_channel_id || "");
  const [trap, setTrap] = useState(center.trap_channel_ids?.[0] || "");
  const [phishing, setPhishing] = useState(center.phishing_action || "delete_only");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dirty = honeypot !== (center.honeypot_channel_id || "") || trap !== (center.trap_channel_ids?.[0] || "") || phishing !== (center.phishing_action || "delete_only");

  async function save() {
    setSaving(true);
    setError(null);
    try {
      await api.updateSecurityCenter(guildId, {
        honeypot_set: true,
        honeypot_channel_id: honeypot || null,
        trap_channel_ids: trap ? [trap] : [],
        phishing_action: phishing,
      });
      await onChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Settings could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="space-y-4">
      <section className="border border-line p-3">
        <h2 className="text-section text-fg-1">Human honeypot</h2>
        <p className="text-small text-fg-2">A visible channel for compromised human accounts. Staff, trusted people, and bots are exempt. A post is removed and recorded. CLS does not ban, kick, or strip roles while ENFORCE is locked.</p>
        <p className="mt-2 text-small text-fg-1">Put a warning in the channel: this channel is a trap. Do not post here.</p>
        <div className="mt-3 max-w-sm">
          <ChannelPicker channels={channels} value={honeypot} onChange={setHoneypot} required={["view_channel", "send_messages"]} intent="mutate" capabilities={data.permission_health?.channels} />
        </div>
      </section>
      <section className="border border-line p-3">
        <h2 className="text-section text-fg-1">Bot trap</h2>
        <p className="text-small text-fg-2">This watches untrusted bots and webhooks. It does not protect against a compromised human account. Use the human honeypot for that.</p>
        <div className="mt-3 max-w-sm">
          <ChannelPicker channels={channels} value={trap} onChange={setTrap} required={["view_channel"]} intent="display" capabilities={data.permission_health?.channels} />
        </div>
      </section>
      <section className="border border-line p-3">
        <h2 className="text-section text-fg-1">Phishing</h2>
        <p className="text-small text-fg-2">CLS deletes the message, records the incident, and reports the result. If Manage Messages is missing, the incident says Failed — Missing Manage Messages.</p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Button type="button" variant={phishing === "delete_only" ? "secondary" : "ghost"} onClick={() => setPhishing("delete_only")}>Delete message</Button>
          {["delete_timeout", "kick", "ban"].map((action) => (
            <span key={action} className="inline-flex items-center gap-1 border border-locked/40 bg-locked/10 px-2 py-1 text-small text-locked" aria-disabled="true">
              <Lock className="size-3" aria-hidden="true" />
              {action === "delete_timeout" ? "Timeout" : action === "kick" ? "Kick" : "Ban"} locked
            </span>
          ))}
        </div>
      </section>
      <SaveBar dirty={dirty} saving={saving} error={error} onSave={() => void save()} onDiscard={() => { setHoneypot(center.honeypot_channel_id || ""); setTrap(center.trap_channel_ids?.[0] || ""); setPhishing(center.phishing_action || "delete_only"); }} />
    </div>
  );
}

function Quarantine({ guildId, data, isRoot, onChange }: { guildId: string; data: any; isRoot: boolean; onChange: () => void }) {
  const [pending, setPending] = useState<string | null>(null);
  const [results, setResults] = useState<any[] | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const rows: any[] = data.quarantines || [];

  async function release(userId: string) {
    if (pending !== userId) {
      setPending(userId);
      return;
    }
    try {
      const body = await api.releaseQuarantine(guildId, userId);
      setResults(body.results || []);
      setMessage(body.status === "RELEASED" ? "Roles that could be restored were restored." : body.status === "PARTIAL" ? "Some roles were restored. The rest stay listed." : "Release did not finish. The reasons are below.");
      onChange();
    } catch (err) {
      setMessage(err instanceof Error ? err.message : "Release failed.");
      setResults(null);
    }
    setPending(null);
  }

  return (
    <div className="space-y-4">
      <DataTable
        rows={rows}
        page={1}
        pages={1}
        pageSize={25}
        total={rows.length}
        onPageChange={() => undefined}
        onPageSizeChange={() => undefined}
        getRowId={(row) => row.user_id}
        emptyTitle="No quarantined members"
        emptyDescription="CLS has no open quarantine records for this server."
        columns={[
          { key: "member", header: "Member", cell: (row) => row.user_id },
          { key: "status", header: "Status", cell: (row) => row.status_label },
          { key: "incident", header: "Incident", cell: (row) => row.incident_id || "None" },
          { key: "at", header: "Quarantined", cell: (row) => row.quarantined_at || "" },
          { key: "roles", header: "Removed roles", cell: (row) => (row.removed_role_ids || []).length },
          { key: "action", header: "", cell: (row) => isRoot ? <Button type="button" onClick={() => void release(row.user_id)}>{pending === row.user_id ? "Confirm release" : "Release"}</Button> : <span className="text-locked">Root only</span> },
        ]}
      />
      {message ? <p className="text-small text-fg-1">{message}</p> : null}
      <div className="space-y-2">{(results || []).map((row, index) => <ActionResultView key={index} result={resultOf(row)} />)}</div>
      <section className="border border-line p-3">
        <h2 className="text-section text-fg-1">Recovery</h2>
        <p className="text-small text-fg-2">{data.recovery?.latest_snapshot_at ? `Latest snapshot ${data.recovery.latest_snapshot_at}.` : "No snapshot is stored."} Guild restore stays locked.</p>
        <Link className="mt-2 inline-flex text-small text-fg-1 underline" href={`/dashboard/guild/${guildId}/recovery`}>Open recovery dry-run</Link>
      </section>
    </div>
  );
}

function Settings({ guildId, data, isRoot, onChange }: { guildId: string; data: any; isRoot: boolean; onChange: () => Promise<void> }) {
  const [humanOn, setHumanOn] = useState(data.human_mode !== "OFF");
  const [botOn, setBotOn] = useState(data.bot_mode !== "OFF");
  const [reason, setReason] = useState("");
  const [minutes, setMinutes] = useState("30");
  const [pending, setPending] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [alert, setAlert] = useState<ActionResult | null>(null);
  const dirty = humanOn !== (data.human_mode !== "OFF") || botOn !== (data.bot_mode !== "OFF");

  async function save() {
    setSaving(true);
    setError(null);
    try {
      let version = data.version;
      if (humanOn !== (data.human_mode !== "OFF")) {
        const row = await api.setSecurityMode(guildId, { subsystem: "human", mode: humanOn ? "OBSERVE" : "OFF", expected_version: version });
        version = row.version;
      }
      if (botOn !== (data.bot_mode !== "OFF")) {
        await api.setSecurityMode(guildId, { subsystem: "bot", mode: botOn ? "OBSERVE" : "OFF", expected_version: version });
      }
      await onChange();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Mode could not be saved.");
    } finally {
      setSaving(false);
    }
  }

  async function start() {
    if (!pending) {
      setPending(true);
      return;
    }
    await api.startSecurityMaintenance(guildId, { reason, duration_s: Number(minutes) * 60 });
    setPending(false);
    await onChange();
  }

  return (
    <div className="space-y-4">
      <section className="border border-line p-3">
        <h2 className="text-section text-fg-1">Protection mode</h2>
        <label className="mt-2 flex items-center gap-2 text-small"><input type="checkbox" checked={humanOn} disabled={!isRoot} onChange={(event) => setHumanOn(event.target.checked)} /> Human protection observes</label>
        <label className="mt-2 flex items-center gap-2 text-small"><input type="checkbox" checked={botOn} disabled={!isRoot} onChange={(event) => setBotOn(event.target.checked)} /> Bot protection observes</label>
        {isRoot ? null : <p className="mt-2 text-small text-locked">Mode changes are Root only.</p>}
        <p className="mt-3 inline-flex items-center gap-1 border border-locked/40 bg-locked/10 px-2 py-1 text-small text-locked" aria-disabled="true"><Lock className="size-3" aria-hidden="true" /> ENFORCE is locked for this deployment</p>
      </section>
      <section className="border border-line p-3">
        <h2 className="text-section text-fg-1">Maintenance</h2>
        <p className="text-small text-fg-2">Maintenance moves enforcement to observe. It does not turn security off. The longest window is 60 minutes.</p>
        {data.maintenance ? <p className="mt-2 text-small text-fg-1">Active until {data.maintenance.ends_at}. {data.maintenance.reason}</p> : null}
        {isRoot ? (
          <div className="mt-3 grid gap-2 md:grid-cols-3">
            <Input aria-label="Maintenance reason" placeholder="Reason" value={reason} onChange={(event) => setReason(event.target.value)} />
            <Input aria-label="Minutes" placeholder="Minutes" value={minutes} onChange={(event) => setMinutes(event.target.value)} />
            <Button type="button" onClick={() => void start()}>{pending ? "Confirm maintenance" : "Start maintenance"}</Button>
            {data.maintenance ? <Button type="button" variant="secondary" onClick={() => void api.endSecurityMaintenance(guildId, reason || "Ended from Security Center").then(onChange)}>End maintenance</Button> : null}
          </div>
        ) : <p className="mt-2 text-small text-locked">Maintenance is Root only.</p>}
      </section>
      <section className="border border-line p-3">
        <h2 className="text-section text-fg-1">Ops alerts</h2>
        <p className="text-small text-fg-2">Destination: {data.ops?.destination_label}. Alerts only go to the configured Ops channel. This server cannot pick a channel in another server.</p>
        <p className="text-caption text-fg-3">{data.ops?.last ? `Last ${data.ops.last.status} at ${data.ops.last.at}` : "No delivery recorded."} Pending: {data.ops?.pending_alerts ?? 0}</p>
        {isRoot ? <Button type="button" className="mt-2" onClick={() => void api.testSecurityAlert(guildId).then((body) => setAlert(resultOf(body)))}>Send test</Button> : null}
        {alert ? <div className="mt-2"><ActionResultView result={alert} /></div> : null}
      </section>
      <SaveBar dirty={dirty} saving={saving} error={error} onSave={() => void save()} onDiscard={() => { setHumanOn(data.human_mode !== "OFF"); setBotOn(data.bot_mode !== "OFF"); }} />
    </div>
  );
}
