"use client";

import React, { useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { ChannelPicker, RolePicker, type ChannelOption, type RoleOption } from "@/components/discord/channel-picker";
import { DataTable } from "@/components/platform/data-table";
import { DetailsDrawer } from "@/components/platform/details-drawer";
import { HealthBadge } from "@/components/platform/health";
import { LoadError } from "@/components/platform/load-error";
import { SaveBar } from "@/components/settings/save-bar";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";
import { api } from "@/lib/api";
import type { PageSize } from "@/lib/pagination";

type CommandRow = {
  id: string;
  name: string;
  display_name: string;
  module: string;
  module_id: string;
  description: string;
  usage: string;
  aliases: string[];
  command_type: "slash" | "prefix" | "hybrid";
  audience: string;
  audience_label: string;
  permissions: string[];
  cooldown: { rate: number; per: number } | null;
  cooldown_configurable: boolean;
  visibility_supported: boolean;
  autodelete_supported: boolean;
  enabled: boolean;
  module_enabled: boolean;
  allowed_role_ids: string[];
  blocked_role_ids: string[];
  allowed_channel_ids: string[];
  blocked_channel_ids: string[];
  restricted: boolean;
  policy_scope: "own" | "inherited";
  runtime_status: string;
  source: string;
};

type ModuleCard = {
  id: string;
  name: string;
  description: string;
  enabled: boolean;
  enabled_commands: number;
  disabled_commands: number;
  restricted_commands: number;
  command_count: number;
  health: { status: "healthy" | "warning" | "error" | "locked" | "unavailable" };
};

type Catalog = {
  overview: {
    active_modules: number;
    module_count: number;
    enabled_commands: number;
    disabled_commands: number;
    restricted_commands: number;
    prefix_commands: number;
    slash_commands: number;
    hybrid_commands: number;
    catalog_status: string;
    layers: string;
  };
  modules: ModuleCard[];
  commands: CommandRow[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
  tree?: Array<{ name: string; command?: CommandRow; children: CommandRow[] }>;
};

type Draft = {
  enabled: boolean;
  allowed_role_ids: string[];
  blocked_role_ids: string[];
  allowed_channel_ids: string[];
  blocked_channel_ids: string[];
};

const VIEWS = [
  { id: "overview", label: "Overview" },
  { id: "modules", label: "Modules" },
  { id: "commands", label: "All commands" },
] as const;

function statusLabel(row: CommandRow) {
  if (!row.module_enabled) return "Module off";
  return row.enabled ? "Enabled" : "Disabled";
}

function restrictionLabel(row: CommandRow) {
  if (!row.restricted) return "No extra limits";
  const parts = [];
  if (row.allowed_role_ids.length) parts.push(`${row.allowed_role_ids.length} allowed roles`);
  if (row.blocked_role_ids.length) parts.push(`${row.blocked_role_ids.length} blocked roles`);
  if (row.allowed_channel_ids.length) parts.push(`${row.allowed_channel_ids.length} channels`);
  if (row.blocked_channel_ids.length) parts.push(`${row.blocked_channel_ids.length} excluded channels`);
  return parts.join(" · ") || "Restricted";
}

function sameDraft(row: CommandRow, draft: Draft) {
  const list = (values: string[]) => values.join(",");
  return (
    row.enabled === draft.enabled &&
    list(row.allowed_role_ids) === list(draft.allowed_role_ids) &&
    list(row.blocked_role_ids) === list(draft.blocked_role_ids) &&
    list(row.allowed_channel_ids) === list(draft.allowed_channel_ids) &&
    list(row.blocked_channel_ids) === list(draft.blocked_channel_ids)
  );
}

export function CommandsWorkspace({
  guildId,
  initial,
  initialError,
  channels,
  roles,
}: {
  guildId: string;
  initial: Catalog | null;
  initialError: string | null;
  channels: ChannelOption[];
  roles: RoleOption[];
}) {
  const router = useRouter();
  const [view, setView] = useState<(typeof VIEWS)[number]["id"]>("overview");
  const [data, setData] = useState<Catalog | null>(initial);
  const [error, setError] = useState<string | null>(initialError);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState("");
  const [moduleId, setModuleId] = useState("");
  const [audience, setAudience] = useState("");
  const [kind, setKind] = useState("");
  const [enabled, setEnabled] = useState("");
  const [restricted, setRestricted] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState<PageSize>(25);
  const [selected, setSelected] = useState<CommandRow | null>(null);
  const [draft, setDraft] = useState<Draft | null>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const [picked, setPicked] = useState<string[]>([]);
  const [confirm, setConfirm] = useState<string | null>(null);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [tree, setTree] = useState<Catalog["tree"]>([]);
  const [accessCommand, setAccessCommand] = useState("");
  const [accessRole, setAccessRole] = useState("");
  const [accessChannel, setAccessChannel] = useState("");
  const [accessResult, setAccessResult] = useState<any>(null);
  const [roleAdd, setRoleAdd] = useState("");
  const [blockedAdd, setBlockedAdd] = useState("");
  const [channelAdd, setChannelAdd] = useState("");
  const [blockedChannelAdd, setBlockedChannelAdd] = useState("");
  const [bulkChannel, setBulkChannel] = useState("");
  const [bulkRole, setBulkRole] = useState("");

  const roleName = (id: string) => roles.find((role) => role.id === id)?.name || id;
  const channelName = (id: string) => channels.find((channel) => channel.id === id)?.name || id;

  async function reload(next?: { page?: number; pageSize?: PageSize; module?: string; viewTree?: boolean }) {
    const currentPage = next?.page ?? page;
    const size = next?.pageSize ?? pageSize;
    const moduleFilter = next?.module ?? moduleId;
    const params = new URLSearchParams();
    params.set("page", String(currentPage));
    params.set("page_size", String(size));
    if (query.trim()) params.set("q", query.trim());
    if (moduleFilter) params.set("module", moduleFilter);
    if (audience) params.set("audience", audience);
    if (kind) params.set("kind", kind);
    if (enabled) params.set("enabled", enabled);
    if (restricted) params.set("restricted", restricted);
    if (next?.viewTree) params.set("tree", "1");
    setLoading(true);
    try {
      const body = (await api.getCommands(guildId, `?${params.toString()}`)) as Catalog;
      setData(body);
      setError(null);
      if (next?.viewTree) setTree(body.tree || []);
      if (selected) {
        const fresh = body.commands.find((row) => row.name === selected.name);
        if (fresh) {
          setSelected(fresh);
          setDraft({
            enabled: fresh.enabled,
            allowed_role_ids: fresh.allowed_role_ids,
            blocked_role_ids: fresh.blocked_role_ids,
            allowed_channel_ids: fresh.allowed_channel_ids,
            blocked_channel_ids: fresh.blocked_channel_ids,
          });
        }
      }
    } catch {
      setError("Commands could not be loaded");
    } finally {
      setLoading(false);
    }
  }

  function openCommand(row: CommandRow) {
    setSelected(row);
    setDraft({
      enabled: row.enabled,
      allowed_role_ids: [...row.allowed_role_ids],
      blocked_role_ids: [...row.blocked_role_ids],
      allowed_channel_ids: [...row.allowed_channel_ids],
      blocked_channel_ids: [...row.blocked_channel_ids],
    });
    setSaveError(null);
  }

  async function savePolicy() {
    if (!selected || !draft) return;
    setSaving(true);
    setSaveError(null);
    try {
      await api.updateCommand(guildId, { command_name: selected.name, ...draft });
      toast.success("Command policy saved");
      await reload();
    } catch (err) {
      setSaveError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  }

  async function toggleModule(module: ModuleCard, enabledFlag: boolean) {
    if (!enabledFlag && module.command_count >= 8 && confirm !== module.id) {
      setConfirm(module.id);
      return;
    }
    setConfirm(null);
    try {
      await api.setCommandModule(guildId, { module_id: module.id, enabled: enabledFlag });
      toast.success(enabledFlag ? `${module.name} enabled` : `${module.name} disabled`);
      await reload();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Module update failed");
    }
  }

  async function expandModule(id: string) {
    if (expanded === id) {
      setExpanded(null);
      return;
    }
    setExpanded(id);
    const params = new URLSearchParams({ module: id, page: "1", page_size: "100", tree: "1" });
    try {
      const body = (await api.getCommands(guildId, `?${params.toString()}`)) as Catalog;
      setTree(body.tree || []);
    } catch {
      setError("Commands could not be loaded");
    }
  }

  async function runBulk(action: string, extra?: { allowed_channel_ids?: string[]; blocked_role_ids?: string[] }) {
    if (!picked.length) return;
    const needsConfirm = action === "disable" || action === "channels" || action === "block_role" || action === "reset";
    if (needsConfirm && confirm !== `bulk-${action}`) {
      setConfirm(`bulk-${action}`);
      return;
    }
    setConfirm(null);
    try {
      const result = await api.bulkCommands(guildId, { action, command_names: picked, ...extra });
      toast.success(`${result.affected} commands updated`);
      setPicked([]);
      await reload();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Bulk update failed");
    }
  }

  async function checkAccess() {
    if (!accessCommand || !accessRole || !accessChannel) return;
    try {
      const result = await api.checkCommandAccess(guildId, {
        command_name: accessCommand,
        role_ids: [accessRole],
        channel_id: accessChannel,
      });
      setAccessResult(result);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Access check failed");
    }
  }

  const dirty = selected && draft ? !sameDraft(selected, draft) : false;
  const modules = data?.modules || [];
  const overview = data?.overview;

  const columns = useMemo(
    () => [
      {
        key: "pick",
        header: "",
        cell: (row: CommandRow) => (
          <input
            type="checkbox"
            aria-label={`Select ${row.display_name}`}
            checked={picked.includes(row.name)}
            onClick={(event) => event.stopPropagation()}
            onChange={() =>
              setPicked((current) => (current.includes(row.name) ? current.filter((name) => name !== row.name) : [...current, row.name]))
            }
          />
        ),
      },
      {
        key: "command",
        header: "Command",
        cell: (row: CommandRow) => (
          <span className="block min-w-0">
            <span className="block truncate text-fg-1">{row.display_name}</span>
            <span className="block truncate text-small text-fg-3">{row.policy_scope === "own" ? "Own policy" : "Inherited"}</span>
          </span>
        ),
      },
      { key: "description", header: "Description", cell: (row: CommandRow) => <span className="line-clamp-2">{row.description}</span> },
      { key: "module", header: "Module", cell: (row: CommandRow) => row.module },
      { key: "audience", header: "Audience", cell: (row: CommandRow) => row.audience_label },
      { key: "type", header: "Type", cell: (row: CommandRow) => row.command_type },
      { key: "status", header: "Status", cell: (row: CommandRow) => statusLabel(row) },
      { key: "limits", header: "Restrictions", cell: (row: CommandRow) => restrictionLabel(row) },
    ],
    [picked],
  );

  if (initialError && !data) {
    return <LoadError title="Commands" error={initialError} />;
  }

  return (
    <div className="min-w-0 max-w-full">
      <PageHeader title="Commands" description="Manage what CLS commands are available, who can use them, and where." />
      <div className="mb-4 flex flex-wrap gap-2" role="tablist">
        {VIEWS.map((item) => (
          <button
            key={item.id}
            type="button"
            role="tab"
            aria-selected={view === item.id}
            className={`motion-safe:transition-colors rounded-xs border px-3 py-1.5 text-small ${view === item.id ? "border-line-strong bg-surface text-fg-1" : "border-line text-fg-2 hover:text-fg-1"}`}
            onClick={() => setView(item.id)}
          >
            {item.label}
          </button>
        ))}
      </div>

      {error ? (
        <LoadError title="Commands" error={error} />
      ) : null}

      {view === "overview" && overview ? (
        <section className="grid gap-4">
          <p className="max-w-3xl text-small text-fg-2">{overview.layers}</p>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            {[
              ["Active modules", `${overview.active_modules} / ${overview.module_count}`],
              ["Enabled commands", String(overview.enabled_commands)],
              ["Disabled commands", String(overview.disabled_commands)],
              ["With restrictions", String(overview.restricted_commands)],
            ].map(([label, value]) => (
              <div key={label} className="rounded-xs border border-line px-3 py-3">
                <p className="text-small text-fg-3">{label}</p>
                <p className="text-section text-fg-1">{value}</p>
              </div>
            ))}
          </div>
          <p className="text-small text-fg-2">
            Catalog status: {overview.catalog_status}. {overview.hybrid_commands} hybrid, {overview.slash_commands} slash, {overview.prefix_commands} prefix.
            Prefix-only commands stay available. New professional commands are slash-first.
          </p>
          <div className="flex flex-wrap gap-2">
            <Button type="button" onClick={() => setView("modules")}>Browse modules</Button>
            <Button type="button" variant="secondary" onClick={() => setView("commands")}>Browse commands</Button>
            <Button type="button" variant="secondary" onClick={() => document.getElementById("access-check")?.scrollIntoView({ behavior: "smooth" })}>
              Check access
            </Button>
          </div>
          <section id="access-check" className="rounded-xs border border-line p-3">
            <h2 className="text-section text-fg-1">Can this role use this command here?</h2>
            <p className="mb-3 text-small text-fg-2">Uses the same policy the bot enforces when someone runs the command.</p>
            <div className="grid gap-3 md:grid-cols-3">
              <Input value={accessCommand} placeholder="Command, such as /ban" onChange={(event) => setAccessCommand(event.target.value.replace(/^\//, ""))} />
              <RolePicker roles={roles} value={accessRole} onChange={setAccessRole} allowEmpty />
              <ChannelPicker channels={channels} value={accessChannel} onChange={setAccessChannel} />
            </div>
            <Button type="button" className="mt-3" onClick={checkAccess}>Check access</Button>
            {accessResult ? (
              <div className="mt-3 text-small">
                <p className="text-fg-1">{accessResult.allowed ? "YES — Allowed" : `NO — ${accessResult.message}`}</p>
                <ul className="mt-2 space-y-1 text-fg-2">
                  {(accessResult.steps || []).map((step: { ok: boolean; label: string }) => (
                    <li key={step.label}>{step.ok ? "Allowed because" : "Denied because"}: {step.label}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </section>
        </section>
      ) : null}

      {view === "modules" ? (
        <section className="grid gap-3">
          {modules.map((module) => (
            <article key={module.id} className="motion-safe:transition-colors rounded-xs border border-line p-3 hover:border-line-strong">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="min-w-0">
                  <h2 className="text-section text-fg-1">{module.name}</h2>
                  <p className="text-small text-fg-2">{module.description}</p>
                  <p className="mt-1 text-small text-fg-3">
                    {module.enabled_commands} enabled · {module.disabled_commands} disabled · {module.restricted_commands} restricted
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <HealthBadge status={module.health.status} />
                  <Button type="button" variant="secondary" onClick={() => toggleModule(module, !module.enabled)}>
                    {module.enabled ? "Disable module" : "Enable module"}
                  </Button>
                </div>
              </div>
              {confirm === module.id ? (
                <p className="mt-2 text-small text-fg-2">
                  Disable {module.command_count} commands in {module.name}? Their individual settings stay saved.
                  <Button type="button" className="ms-2" onClick={() => toggleModule(module, false)}>Disable</Button>
                </p>
              ) : null}
              <button type="button" className="mt-2 text-small text-fg-2 underline-offset-2 hover:underline" onClick={() => expandModule(module.id)}>
                {expanded === module.id ? "Hide commands" : "Show command tree"}
              </button>
              {expanded === module.id ? (
                <ul className="mt-2 space-y-2 text-small">
                  {(tree || []).map((group) => (
                    <li key={group.name}>
                      <button type="button" className="text-fg-1" onClick={() => group.command && openCommand(group.command)}>
                        {group.name}
                        {group.command ? ` · ${group.command.policy_scope === "own" ? "Own policy" : "Inherited"}` : ""}
                      </button>
                      {group.children?.length ? (
                        <ul className="ms-4 mt-1 space-y-1 border-s border-line ps-3">
                          {group.children.map((child) => (
                            <li key={child.name}>
                              <button type="button" className="text-fg-2" onClick={() => openCommand(child)}>
                                {child.display_name} · {child.policy_scope === "own" ? "Own policy" : "Inherited"}
                              </button>
                            </li>
                          ))}
                        </ul>
                      ) : null}
                    </li>
                  ))}
                </ul>
              ) : null}
            </article>
          ))}
        </section>
      ) : null}

      {view === "commands" && data ? (
        <section className="min-w-0">
          <div className="mb-3 grid gap-2 md:grid-cols-3 xl:grid-cols-6">
            <Input
              value={query}
              placeholder="Search name, description, alias"
              onChange={(event) => setQuery(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  setPage(1);
                  void reload({ page: 1 });
                }
              }}
            />
            <Select value={moduleId} onValueChange={(value) => { setModuleId(value); setPage(1); }} placeholder="Module" options={[{ value: "", label: "All modules" }, ...modules.map((item) => ({ value: item.id, label: item.name }))]} />
            <Select value={audience} onValueChange={setAudience} placeholder="Audience" options={[{ value: "", label: "Any audience" }, { value: "guild_admin", label: "Guild Admin" }, { value: "staff", label: "Staff / Moderator" }, { value: "member", label: "Member" }]} />
            <Select value={kind} onValueChange={setKind} placeholder="Type" options={[{ value: "", label: "Any type" }, { value: "slash", label: "Slash" }, { value: "prefix", label: "Prefix" }, { value: "hybrid", label: "Hybrid" }]} />
            <Select value={enabled} onValueChange={setEnabled} placeholder="Status" options={[{ value: "", label: "Enabled and disabled" }, { value: "on", label: "Enabled" }, { value: "off", label: "Disabled" }]} />
            <Select value={restricted} onValueChange={setRestricted} placeholder="Restrictions" options={[{ value: "", label: "Any restrictions" }, { value: "yes", label: "Restricted" }, { value: "no", label: "Unrestricted" }]} />
          </div>
          <div className="mb-3">
            <Button type="button" onClick={() => { setPage(1); void reload({ page: 1 }); }}>Apply filters</Button>
          </div>
          {picked.length ? (
            <div className="mb-3 flex flex-wrap items-center gap-2 text-small">
              <span>{picked.length} selected</span>
              <Button type="button" variant="secondary" onClick={() => runBulk("enable")}>Enable selected</Button>
              <Button type="button" variant="secondary" onClick={() => runBulk("disable")}>Disable selected</Button>
              <Button type="button" variant="secondary" onClick={() => runBulk("reset")}>Reset selected</Button>
              {confirm?.startsWith("bulk-") ? (
                <Button type="button" onClick={() => {
                  const action = confirm.replace("bulk-", "");
                  void runBulk(action, action === "channels" ? { allowed_channel_ids: bulkChannel ? [bulkChannel] : [] } : action === "block_role" ? { blocked_role_ids: bulkRole ? [bulkRole] : [] } : undefined);
                }}>Confirm {picked.length}</Button>
              ) : null}
              <div className="flex min-w-0 flex-wrap items-center gap-2">
                <div className="w-44">
                  <ChannelPicker channels={channels} value={bulkChannel} onChange={setBulkChannel} />
                </div>
                <Button type="button" variant="secondary" onClick={() => runBulk("channels", { allowed_channel_ids: bulkChannel ? [bulkChannel] : [] })}>Set channel restriction</Button>
                <div className="w-44">
                  <RolePicker roles={roles} value={bulkRole} onChange={setBulkRole} allowEmpty />
                </div>
                <Button type="button" variant="secondary" onClick={() => runBulk("block_role", { blocked_role_ids: bulkRole ? [bulkRole] : [] })}>Add blocked role</Button>
              </div>
            </div>
          ) : null}
          <DataTable
            rows={data.commands}
            columns={columns}
            getRowId={(row) => row.name}
            page={data.page}
            pages={data.pages}
            pageSize={(data.page_size as PageSize) || pageSize}
            total={data.total}
            loading={loading}
            error={error}
            onRetry={() => router.refresh()}
            onPageChange={(next) => { setPage(next); void reload({ page: next }); }}
            onPageSizeChange={(size) => { setPageSize(size); setPage(1); void reload({ page: 1, pageSize: size }); }}
            selectedId={selected?.name}
            onSelect={(id) => {
              const row = data.commands.find((item) => item.name === id);
              if (row) openCommand(row);
            }}
            emptyTitle="No commands match"
            emptyDescription="Try another search or filter. Root and retired commands are not listed here."
          />
        </section>
      ) : null}

      <DetailsDrawer
        open={Boolean(selected && draft)}
        onOpenChange={(open) => {
          if (!open) {
            setSelected(null);
            setDraft(null);
          }
        }}
        title={selected?.display_name || "Command"}
        summary={null}
        sections={selected && draft ? [
          {
            id: "overview",
            label: "Overview",
            content: (
              <div className="space-y-2 text-small">
                <p>{selected.description}</p>
                <p>Module: {selected.module}</p>
                <p>Audience: {selected.audience_label}</p>
                <p>Type: {selected.command_type}</p>
                <p>Status: {statusLabel(selected)}</p>
              </div>
            ),
          },
          {
            id: "usage",
            label: "Usage",
            content: (
              <div className="space-y-2 text-small">
                <p>{selected.usage}</p>
                {selected.aliases.length ? <p>Aliases: {selected.aliases.join(", ")}</p> : <p>No public aliases.</p>}
              </div>
            ),
          },
          {
            id: "access",
            label: "Access",
            content: (
              <div className="space-y-3 text-small">
                <label className="flex items-center gap-2">
                  <input type="checkbox" checked={draft.enabled} onChange={(event) => setDraft({ ...draft, enabled: event.target.checked })} />
                  Enabled
                </label>
                <p>Blocked roles and blocked channels win. If allowed roles are set, the member must have one. If allowed channels are set, the command only runs there. A parent command's limits still apply.</p>
                <p>{selected.policy_scope === "own" ? "Own policy" : "Inherited"} — {selected.policy_scope === "own" ? "these settings apply in addition to any parent command." : "no settings are stored on this command yet."}</p>
                <p className="text-fg-3">Allowed roles</p>
                <RolePicker roles={roles} value={roleAdd} onChange={(id) => { setRoleAdd(id); if (id && !draft.allowed_role_ids.includes(id)) setDraft({ ...draft, allowed_role_ids: [...draft.allowed_role_ids, id] }); }} allowEmpty />
                <p>{draft.allowed_role_ids.map(roleName).join(", ") || "Anyone"}</p>
                <p className="text-fg-3">Blocked roles</p>
                <RolePicker roles={roles} value={blockedAdd} onChange={(id) => { setBlockedAdd(id); if (id && !draft.blocked_role_ids.includes(id)) setDraft({ ...draft, blocked_role_ids: [...draft.blocked_role_ids, id] }); }} allowEmpty />
                <p>{draft.blocked_role_ids.map(roleName).join(", ") || "None"}</p>
                <p className="text-fg-3">Allowed channels</p>
                <ChannelPicker channels={channels} value={channelAdd} onChange={(id) => { setChannelAdd(id); if (id && !draft.allowed_channel_ids.includes(id)) setDraft({ ...draft, allowed_channel_ids: [...draft.allowed_channel_ids, id] }); }} />
                <p>{draft.allowed_channel_ids.map((id) => `#${channelName(id)}`).join(", ") || "Every channel"}</p>
                <p className="text-fg-3">Blocked channels</p>
                <ChannelPicker channels={channels} value={blockedChannelAdd} onChange={(id) => { setBlockedChannelAdd(id); if (id && !draft.blocked_channel_ids.includes(id)) setDraft({ ...draft, blocked_channel_ids: [...draft.blocked_channel_ids, id] }); }} />
                <p>{draft.blocked_channel_ids.map((id) => `#${channelName(id)}`).join(", ") || "None"}</p>
                <SaveBar dirty={dirty} saving={saving} error={saveError} onSave={savePolicy} onDiscard={() => openCommand(selected)} />
              </div>
            ),
          },
          {
            id: "behavior",
            label: "Behavior",
            content: (
              <div className="space-y-2 text-small text-fg-2">
                <p>
                  {selected.cooldown
                    ? `Runtime cooldown: ${selected.cooldown.rate} uses / ${selected.cooldown.per} seconds. This is defined on the command and is not editable here.`
                    : "No cooldown is defined for this command."}
                </p>
                <p>Response visibility is not offered. This command does not read a public or ephemeral setting from CLS.</p>
                <p>Invocation cleanup is not offered. CLS will not delete the command message or the reply.</p>
              </div>
            ),
          },
          {
            id: "permissions",
            label: "Permissions",
            content: (
              <div className="space-y-2 text-small text-fg-2">
                <p>Discord permissions: {selected.permissions.length ? selected.permissions.join(", ") : "None declared on the command."}</p>
                <p>CLS policy is the enabled switch, roles, and channels on the Access tab. CLS does not write Discord's integration permissions.</p>
                <p>Health: {selected.runtime_status}.</p>
              </div>
            ),
          },
          {
            id: "developer",
            label: "Developer",
            content: (
              <div className="space-y-1 text-small text-fg-3">
                <p>Qualified name: {selected.name}</p>
                <p>Source: {selected.source}</p>
                <p>Runtime: {selected.runtime_status}</p>
              </div>
            ),
          },
        ] : undefined}
      />
    </div>
  );
}
