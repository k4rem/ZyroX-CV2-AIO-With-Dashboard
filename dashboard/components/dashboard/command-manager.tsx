"use client";

import React, { useMemo, useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { Input } from "@/components/ui/input";
import { StatusLabel } from "@/components/ui/status";
import { Switch } from "@/components/ui/switch";
import { api } from "@/lib/api";

type CommandRow = {
  name: string;
  module: string;
  description: string;
  dangerous: boolean;
  enabled: boolean;
  allowed_role_ids: string[];
};

export function CommandManager({ guildId, initial }: { guildId: string; initial: CommandRow[] }) {
  const [rows, setRows] = useState(initial);
  const [query, setQuery] = useState("");
  const [moduleName, setModuleName] = useState("");

  const modules = useMemo(() => Array.from(new Set(rows.map((row) => row.module))).sort(), [rows]);
  const visible = rows.filter((row) => {
    const text = `${row.name} ${row.module} ${row.description}`.toLowerCase();
    if (query && !text.includes(query.toLowerCase())) return false;
    if (moduleName && row.module !== moduleName) return false;
    return true;
  });

  const toggle = async (row: CommandRow, enabled: boolean) => {
    setRows((current) => current.map((item) => (item.name === row.name ? { ...item, enabled } : item)));
    try {
      await api.updateCommand(guildId, {
        command_name: row.name,
        enabled,
        allowed_role_ids: row.allowed_role_ids,
      });
    } catch {
      setRows((current) => current.map((item) => (item.name === row.name ? row : item)));
      toast.error("Could not update the command");
    }
  };

  return (
    <div className="space-y-4">
      <PageHeader title="Commands" description="Search, disable, and restrict the commands already loaded by the bot." />
      <div className="flex flex-wrap gap-2">
        <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search commands" />
        <Input value={moduleName} onChange={(event) => setModuleName(event.target.value)} placeholder="Module name" list="command-modules" />
        <datalist id="command-modules">
          {modules.map((name) => (
            <option key={name} value={name} />
          ))}
        </datalist>
      </div>
      <p className="text-small text-fg-3">{visible.length} shown. Disabled commands do not run.</p>
      {visible.length === 0 ? (
        <p className="text-small text-fg-3">No commands match. The bot inventory is empty until it finishes loading.</p>
      ) : (
        <ul className="divide-y divide-line-subtle border border-line-subtle">
          {visible.map((row) => (
            <li key={row.name} className="grid grid-cols-1 gap-2 px-3 py-2 md:grid-cols-[1fr_8rem_10rem_auto] md:items-center">
              <div>
                <p className="font-mono text-small text-fg-1">{row.name}</p>
                <p className="text-caption text-fg-3">{row.module}{row.description ? ` · ${row.description}` : ""}</p>
              </div>
              <div>{row.dangerous ? <StatusLabel status="warning">Dangerous</StatusLabel> : <StatusLabel status="disabled">Standard</StatusLabel>}</div>
              <Input
                value={row.allowed_role_ids.join(",")}
                placeholder="Role IDs"
                onChange={(event) => {
                  const allowed = event.target.value.split(",").map((item) => item.trim()).filter(Boolean);
                  setRows((current) => current.map((item) => (item.name === row.name ? { ...item, allowed_role_ids: allowed } : item)));
                }}
                onBlur={(event) => {
                  const allowed = event.target.value.split(",").map((item) => item.trim()).filter(Boolean);
                  void api
                    .updateCommand(guildId, { command_name: row.name, enabled: row.enabled, allowed_role_ids: allowed })
                    .catch(() => toast.error("Could not update role restrictions"));
                }}
              />
              <Switch checked={row.enabled} aria-label={`${row.name} enabled`} onCheckedChange={(enabled) => void toggle(row, enabled)} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
