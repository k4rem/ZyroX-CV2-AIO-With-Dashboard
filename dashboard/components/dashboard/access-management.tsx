"use client";

import React, { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { toast } from "sonner";

type GrantRow = {
  id: string;
  guild_id: string;
  discord_user_id: string;
  role?: string;
  template_key?: string;
};

export function AccessManagement() {
  const [grants, setGrants] = useState<GrantRow[]>([]);
  const [guildId, setGuildId] = useState("");
  const [userId, setUserId] = useState("");
  const [template, setTemplate] = useState("admin");

  const load = async () => {
    try {
      const data = (await api.listAccessGrants()) as GrantRow[];
      setGrants(data);
    } catch {
      toast.error("Failed to load grants");
    }
  };

  useEffect(() => {
    load();
  }, []);

  const onGrant = async () => {
    try {
      await api.createAccessGrant({
        guild_id: Number(guildId),
        discord_user_id: Number(userId),
        template_key: template,
      });
      toast.success("Grant created");
      setUserId("");
      await load();
    } catch (e: unknown) {
      toast.error(e instanceof Error ? e.message : "Grant failed");
    }
  };

  return (
    <div className="space-y-8 bg-[#141B2D] border border-slate-800 rounded-2xl p-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Input placeholder="Guild ID" value={guildId} onChange={(e) => setGuildId(e.target.value)} />
        <Input placeholder="Discord user ID" value={userId} onChange={(e) => setUserId(e.target.value)} />
        <select
          className="bg-slate-900 border border-slate-700 rounded-md px-3 text-sm text-white"
          value={template}
          onChange={(e) => setTemplate(e.target.value)}
        >
          <option value="admin">Admin</option>
          <option value="moderator">Moderator</option>
          <option value="support">Support</option>
        </select>
        <Button onClick={onGrant}>Grant access</Button>
      </div>
      <div className="space-y-2">
        {grants.map((g) => (
          <div
            key={g.id}
            className="flex items-center justify-between border border-slate-800 rounded-lg px-4 py-3 text-sm text-slate-300"
          >
            <span>
              user {g.discord_user_id} → guild {g.guild_id} ({g.role || g.template_key})
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={async () => {
                await api.revokeAccessGrant(g.id);
                toast.success("Revoked");
                load();
              }}
            >
              Revoke
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
