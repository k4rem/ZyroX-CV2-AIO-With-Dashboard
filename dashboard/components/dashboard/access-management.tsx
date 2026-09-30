"use client";

import React, { useEffect, useMemo, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { PageHeader } from "@/components/dashboard/page-header";
import { CopyIdButton } from "@/components/auth/copy-id-button";
import { ACCESS_TEMPLATES, templateLabel } from "@/lib/accessTemplates";
import { normalizeSnowflakeInput } from "@/lib/snowflake";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { toast } from "sonner";

type GrantRow = {
  id: string;
  guild_id: string;
  discord_user_id: string;
  role?: string;
  template_key?: string;
};

type GuildOption = { id: string; name: string };

export function AccessManagement({ guilds }: { guilds: GuildOption[] }) {
  const [grants, setGrants] = useState<GrantRow[]>([]);
  const [loading, setLoading] = useState(true);
  const [guildId, setGuildId] = useState("");
  const [userId, setUserId] = useState("");
  const [template, setTemplate] = useState("admin");
  const [confirmRevoke, setConfirmRevoke] = useState<GrantRow | null>(null);
  const [revoking, setRevoking] = useState(false);

  const guildNames = useMemo(() => {
    const m = new Map<string, string>();
    for (const g of guilds) m.set(g.id, g.name);
    return m;
  }, [guilds]);

  const load = async () => {
    setLoading(true);
    try {
      const data = (await api.listAccessGrants()) as GrantRow[];
      setGrants(data);
    } catch {
      toast.error("Failed to load grants");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void load();
  }, []);

  const onGrant = async () => {
    const gid = normalizeSnowflakeInput(guildId);
    const uid = normalizeSnowflakeInput(userId);
    if (!gid || !uid) {
      toast.error("Enter valid 17–20 digit server and user IDs");
      return;
    }
    try {
      await api.createAccessGrant({
        guild_id: gid,
        discord_user_id: uid,
        template_key: template,
      });
      toast.success("Grant created");
      setUserId("");
      await load();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Grant failed");
    }
  };

  const onRevokeConfirmed = async () => {
    if (!confirmRevoke) return;
    setRevoking(true);
    try {
      await api.revokeAccessGrant(confirmRevoke.id);
      toast.success("Access revoked");
      setConfirmRevoke(null);
      await load();
    } catch {
      toast.error("Revoke failed");
    } finally {
      setRevoking(false);
    }
  };

  const selectedTemplate = ACCESS_TEMPLATES.find((t) => t.key === template);

  return (
    <div className="space-y-6">
      <PageHeader
        title="Access management"
        description="Grant or revoke dashboard access by Discord user ID. Root-only."
      />

      <section className="space-y-4 rounded-md border border-line bg-surface-1 p-4">
        <h2 className="text-section-title text-fg-1">New grant</h2>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-4">
          <div className="space-y-1">
            <label htmlFor="grant-guild-id" className="text-caption text-fg-2">
              Guild / server ID
            </label>
            <Input
              id="grant-guild-id"
              placeholder="17–20 digit ID"
              value={guildId}
              onChange={(e) => setGuildId(e.target.value)}
              dir="ltr"
              className="font-mono"
              inputMode="numeric"
              autoComplete="off"
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="grant-user-id" className="text-caption text-fg-2">
              Discord user ID
            </label>
            <Input
              id="grant-user-id"
              placeholder="17–20 digit ID"
              value={userId}
              onChange={(e) => setUserId(e.target.value)}
              dir="ltr"
              className="font-mono"
              inputMode="numeric"
              autoComplete="off"
            />
          </div>
          <div className="space-y-1">
            <label htmlFor="grant-template" className="text-caption text-fg-2">
              Access template
            </label>
            <select
              id="grant-template"
              className="h-9 w-full rounded-md border border-line bg-surface-2 px-3 text-body text-fg-1"
              value={template}
              onChange={(e) => setTemplate(e.target.value)}
            >
              {ACCESS_TEMPLATES.map((t) => (
                <option key={t.key} value={t.key}>
                  {t.label}
                </option>
              ))}
            </select>
          </div>
          <div className="flex items-end">
            <Button onClick={() => void onGrant()}>Grant access</Button>
          </div>
        </div>
        {selectedTemplate && (
          <p className="text-caption text-fg-2">{selectedTemplate.description}</p>
        )}
      </section>

      <section className="rounded-md border border-line bg-surface-1 p-4">
        <div className="mb-3 flex items-center justify-between gap-2">
          <h2 className="text-section-title text-fg-1">Active grants</h2>
          <Button variant="secondary" size="sm" onClick={() => void load()} disabled={loading}>
            Refresh
          </Button>
        </div>
        {loading ? (
          <p className="text-body text-fg-2">Loading grants…</p>
        ) : grants.length === 0 ? (
          <p className="text-body text-fg-2">No active grants.</p>
        ) : (
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>User</TableHead>
                  <TableHead>Server</TableHead>
                  <TableHead>Role</TableHead>
                  <TableHead className="text-end">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {grants.map((g) => {
                  const serverName = guildNames.get(String(g.guild_id));
                  const roleName = g.role ?? templateLabel(g.template_key);
                  return (
                    <TableRow key={g.id}>
                      <TableCell>
                        <div className="flex flex-col gap-1">
                          <span className="font-mono text-body text-fg-1" dir="ltr">
                            {g.discord_user_id}
                          </span>
                          <CopyIdButton value={g.discord_user_id} label="Copy ID" />
                        </div>
                      </TableCell>
                      <TableCell>
                        <div className="min-w-0">
                          {serverName ? (
                            <p className="truncate text-body text-fg-1">{serverName}</p>
                          ) : null}
                          <p className="font-mono text-caption text-fg-3" dir="ltr">
                            {g.guild_id}
                          </p>
                        </div>
                      </TableCell>
                      <TableCell className="text-fg-2">{roleName}</TableCell>
                      <TableCell className="text-end">
                        <Button
                          variant="destructive"
                          size="sm"
                          onClick={() => setConfirmRevoke(g)}
                        >
                          Revoke
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </section>

      <Dialog open={Boolean(confirmRevoke)} onOpenChange={(open) => !open && setConfirmRevoke(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Revoke dashboard access?</DialogTitle>
            <DialogDescription>
              User{" "}
              <span className="font-mono text-fg-1" dir="ltr">
                {confirmRevoke?.discord_user_id}
              </span>{" "}
              will lose access to server{" "}
              <span className="font-mono text-fg-1" dir="ltr">
                {confirmRevoke?.guild_id}
              </span>
              . This takes effect immediately.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter className="gap-2 sm:gap-0">
            <Button variant="secondary" onClick={() => setConfirmRevoke(null)} disabled={revoking}>
              Cancel
            </Button>
            <Button variant="destructive" onClick={() => void onRevokeConfirmed()} disabled={revoking}>
              {revoking ? "Revoking…" : "Revoke access"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
