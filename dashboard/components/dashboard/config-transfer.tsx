"use client";

import { useEffect, useMemo, useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { TRANSFER_STEPS, modeLabel, resultLabel, whenLabel } from "@/lib/configTransfer";
import { ChannelPicker, RolePicker, type ChannelOption } from "@/components/discord/channel-picker";
import { EmojiPicker, type GuildEmoji } from "@/components/discord/emoji-picker";
import { Button } from "@/components/ui/button";
import { Select } from "@/components/ui/select";

type Group = { id: string; label: string; modules: { id: string; label: string; summary: string }[] };
type Resource = { key: string; type: string; name: string; source_id: string; status: string; detail: string; affects: string[]; target_id?: string | null };
type Change = { module: string; label: string; action: string; detail: string };

function explain(err: unknown) {
  return err instanceof Error ? err.message : "That file could not be read.";
}

export function ConfigTransfer({ guildId }: { guildId: string }) {
  const [view, setView] = useState<"export" | "import">("export");
  const [groups, setGroups] = useState<Group[]>([]);
  const [picked, setPicked] = useState<string[]>([]);
  const [bundle, setBundle] = useState<any>(null);
  const [checked, setChecked] = useState<any>(null);
  const [importModules, setImportModules] = useState<string[]>([]);
  const [strategy, setStrategy] = useState("merge");
  const [choices, setChoices] = useState<Record<string, { action: string; target_id?: string; emoji?: string }>>({});
  const [planned, setPlanned] = useState<any>(null);
  const [result, setResult] = useState<any>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [roles, setRoles] = useState<{ id: string; name: string }[]>([]);
  const [channels, setChannels] = useState<ChannelOption[]>([]);
  const [emojis, setEmojis] = useState<GuildEmoji[]>([]);
  const [busy, setBusy] = useState(false);
  const [step, setStep] = useState(0);

  useEffect(() => {
    api.getConfigPreview(guildId).then((body) => {
      setGroups(body.groups || []);
      setPicked((body.groups || []).flatMap((group) => group.modules.map((item) => item.id)));
    }).catch((err) => toast.error(explain(err)));
    api.getRoles(guildId).then(setRoles).catch(() => setRoles([]));
    api.getChannels(guildId).then(setChannels).catch(() => setChannels([]));
    api.listGuildEmojis(guildId).then((body) => setEmojis(body.emojis || [])).catch(() => setEmojis([]));
    api.configHistory(guildId).then((body) => setHistory(body.imports || [])).catch(() => setHistory([]));
  }, [guildId]);

  const selectedSummary = useMemo(() => groups.flatMap((group) => group.modules).filter((item) => picked.includes(item.id)), [groups, picked]);

  async function download() {
    setBusy(true);
    try {
      const body = await api.exportConfig(guildId, picked);
      const blob = new Blob([JSON.stringify(body, null, 2)], { type: "application/json" });
      const link = document.createElement("a");
      link.href = URL.createObjectURL(blob);
      link.download = `cls-config-${guildId}.json`;
      link.click();
      URL.revokeObjectURL(link.href);
      toast.success("Backup downloaded");
    } catch (err) {
      toast.error(explain(err));
    } finally {
      setBusy(false);
    }
  }

  async function readFile(file: File) {
    setResult(null);
    setPlanned(null);
    try {
      const parsed = JSON.parse(await file.text());
      setBundle(parsed);
      const review = await api.validateConfig(guildId, parsed);
      setChecked(review);
      setImportModules(review.modules || []);
      setStep(1);
    } catch (err) {
      setBundle(null);
      setChecked(null);
      toast.error(explain(err));
    }
  }

  async function reviewPlan() {
    setBusy(true);
    try {
      const body = await api.planConfig(guildId, { bundle, modules: importModules, mappings: choices, strategy });
      setPlanned(body);
      setStep(body.resources?.length ? 2 : 3);
    } catch (err) {
      toast.error(explain(err));
    } finally {
      setBusy(false);
    }
  }

  async function applyImport() {
    setBusy(true);
    try {
      const body = await api.applyConfig(guildId, { bundle, modules: importModules, mappings: choices, strategy });
      setResult(body);
      setStep(4);
      if (body.ok) toast.success(body.message);
      else toast.error(body.message);
      const next = await api.configHistory(guildId);
      setHistory(next.imports || []);
    } catch (err) {
      toast.error(explain(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Button type="button" variant={view === "export" ? "default" : "secondary"} onClick={() => setView("export")}>Export</Button>
        <Button type="button" variant={view === "import" ? "default" : "secondary"} onClick={() => setView("import")}>Import</Button>
      </div>

      {view === "export" ? (
        <section className="space-y-4">
          <div className="flex gap-2">
            <Button type="button" variant="secondary" onClick={() => setPicked(groups.flatMap((group) => group.modules.map((item) => item.id)))}>Select all</Button>
            <Button type="button" variant="secondary" onClick={() => setPicked([])}>Clear all</Button>
          </div>
          {groups.map((group) => (
            <div key={group.id} className="space-y-2">
              <h3 className="text-xs uppercase tracking-wide text-muted">{group.label}</h3>
              <div className="grid gap-2 sm:grid-cols-2">
                {group.modules.map((item) => (
                  <label key={item.id} className="flex items-center justify-between gap-3 rounded-md border border-line bg-surface-1 px-3 py-2 text-sm">
                    <span className="flex items-center gap-2">
                      <input type="checkbox" checked={picked.includes(item.id)} onChange={() => setPicked((current) => current.includes(item.id) ? current.filter((id) => id !== item.id) : [...current, item.id])} />
                      {item.label}
                    </span>
                    <span className="text-xs text-muted">{item.summary}</span>
                  </label>
                ))}
              </div>
            </div>
          ))}
          <div className="rounded-md border border-line bg-surface-1 p-3 text-sm">
            {selectedSummary.length ? selectedSummary.map((item) => <p key={item.id}>{item.label}: {item.summary}</p>) : <p className="text-muted">Choose at least one module.</p>}
          </div>
          <Button type="button" onClick={download} disabled={busy || !picked.length}>Download JSON</Button>
        </section>
      ) : (
        <section className="space-y-4">
          <ol className="flex flex-wrap gap-2 text-xs">
            {TRANSFER_STEPS.map((label, index) => (
              <li key={label} className={index === step ? "rounded-md bg-surface-3 px-2 py-1 text-fg-1" : "rounded-md px-2 py-1 text-muted"}>{index + 1}. {label}</li>
            ))}
          </ol>
          <label className="block rounded-md border border-dashed border-line bg-surface-1 p-4 text-sm" onDragOver={(event) => event.preventDefault()} onDrop={(event) => { event.preventDefault(); const file = event.dataTransfer.files?.[0]; if (file) readFile(file); }}>
            Drop a CLS backup here, or choose a file.
            <input className="mt-2 block text-sm" type="file" accept="application/json,.json" onChange={(event) => { const file = event.target.files?.[0]; if (file) readFile(file); }} />
          </label>
          {checked ? (
            <div className="space-y-2 rounded-md border border-line bg-surface-1 p-3 text-sm">
              <p>Source server: {checked.source?.guild_name || "Unnamed server"}</p>
              <p>Export date: {whenLabel(checked.exported_at)}</p>
              <p>Version: {checked.version}</p>
              <p>{modeLabel(checked.mode)}</p>
              <p>Validation: ready</p>
              {(checked.modules || []).map((id: string) => (
                <label key={id} className="flex items-center gap-2">
                  <input type="checkbox" checked={importModules.includes(id)} onChange={() => setImportModules((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id])} />
                  {groups.flatMap((group) => group.modules).find((item) => item.id === id)?.label || id}
                </label>
              ))}
              <Select value={strategy} onValueChange={setStrategy} options={[{ value: "merge", label: "Merge / Update" }, { value: "replace", label: "Replace selected module" }]} />
              {strategy === "replace" ? <p className="text-xs text-amber-300">Replace removes configuration in the selected modules that is not in this backup.</p> : null}
              <Button type="button" onClick={reviewPlan} disabled={busy}>Review changes</Button>
            </div>
          ) : null}
          {planned?.resources?.length ? (
            <div className="space-y-2">
              {planned.resources.map((row: Resource) => (
                <article key={row.key} className="grid gap-2 rounded-md border border-line bg-surface-1 p-3 sm:grid-cols-[1fr_auto_1fr]">
                  <div className="text-sm">
                    <p>{row.type} · {row.name || "Unnamed"}</p>
                    <p className="text-xs text-muted">{row.detail}</p>
                    {(row.affects || []).map((note) => <p key={note} className="text-xs text-muted">{note}</p>)}
                  </div>
                  <span className="text-xs uppercase text-muted">{row.status.replaceAll("_", " ")}</span>
                  <Mapper row={row} roles={roles} channels={channels} emojis={emojis} onChange={(choice) => setChoices((current) => ({ ...current, [row.key]: choice }))} />
                </article>
              ))}
              <Button type="button" variant="secondary" onClick={reviewPlan} disabled={busy}>Update preview</Button>
            </div>
          ) : null}
          {planned?.changes ? (
            <div className="space-y-1 rounded-md border border-line bg-surface-1 p-3 text-sm">
              {planned.changes.map((change: Change) => <p key={change.module}>{change.label}: {change.action} — {change.detail}</p>)}
              <Button type="button" onClick={applyImport} disabled={busy || !planned.ready}>Apply</Button>
            </div>
          ) : null}
          {result ? <p className="text-sm">{resultLabel(result.result)}. {result.message}</p> : null}
          {history.length ? (
            <div className="space-y-1 text-xs text-muted">
              {history.slice(0, 5).map((row) => <p key={row.id}>{whenLabel(row.at)} · {row.source_guild_name || "Unknown server"} · {resultLabel(row.result)}</p>)}
            </div>
          ) : null}
        </section>
      )}
    </div>
  );
}

function destination(row: Resource, roles: { id: string; name: string }[], channels: ChannelOption[], emojis: GuildEmoji[]) {
  const id = row.target_id || "";
  if (row.type === "role") return roles.find((role) => role.id === id)?.name || "Mapped role";
  if (row.type === "emoji") return emojis.find((emoji) => emoji.id === id)?.name || "Mapped emoji";
  return channels.find((channel) => channel.id === id)?.name || "Mapped channel";
}

function Mapper({
  row,
  roles,
  channels,
  emojis,
  onChange,
}: {
  row: Resource;
  roles: { id: string; name: string }[];
  channels: ChannelOption[];
  emojis: GuildEmoji[];
  onChange: (choice: { action: string; target_id?: string; emoji?: string }) => void;
}) {
  if (row.status === "resolved" || row.status === "skip") {
    return <p className="text-sm text-muted">{row.status === "skip" ? "Skipped" : destination(row, roles, channels, emojis)}</p>;
  }
  if (row.type === "emoji") {
    return (
      <div className="space-y-2">
        <EmojiPicker value="" emojis={emojis} onChange={(emoji) => onChange(emoji.startsWith("<") ? { action: "map", target_id: emoji.match(/:(\d+)>$/)?.[1] || "" } : { action: "unicode", emoji })} />
        <Button type="button" variant="secondary" onClick={() => onChange({ action: "skip" })}>Skip emoji</Button>
      </div>
    );
  }
  if (row.type === "role") {
    return (
      <div className="space-y-2">
        <RolePicker roles={roles} value="" onChange={(id) => onChange({ action: "map", target_id: id })} />
        <Button type="button" variant="secondary" onClick={() => onChange({ action: "skip" })}>Skip this resource</Button>
      </div>
    );
  }
  const options = channels.filter((channel) => row.type === "category" ? String(channel.type) === "4" : String(channel.type) !== "4");
  return (
    <div className="space-y-2">
      {row.type === "channel" ? <ChannelPicker channels={channels} value="" onChange={(id) => onChange({ action: "map", target_id: id })} /> : <Select value="" onValueChange={(id) => onChange({ action: "map", target_id: id })} options={options.map((channel) => ({ value: channel.id, label: channel.name }))} placeholder="Choose a category" />}
      <Button type="button" variant="secondary" onClick={() => onChange({ action: "skip" })}>Skip this resource</Button>
    </div>
  );
}
