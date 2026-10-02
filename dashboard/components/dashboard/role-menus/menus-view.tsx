"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { menuModeLabel, menuTypeLabel } from "@/lib/roleMenuModel";
import { PageHeader } from "@/components/dashboard/page-header";
import { Button } from "@/components/ui/button";

function explain(err: unknown) {
  return err instanceof Error ? err.message : "That menu action failed.";
}

export function MenusView({
  guildId,
  menus,
  channelNames,
}: {
  guildId: string;
  menus: Array<Record<string, any>>;
  channelNames: Record<string, string>;
}) {
  const router = useRouter();
  const [busy, setBusy] = useState(false);
  const base = `/dashboard/guild/${guildId}/reactionroles`;

  async function run(task: () => Promise<unknown>, done: string) {
    setBusy(true);
    try {
      await task();
      toast.success(done);
      router.refresh();
    } catch (err) {
      toast.error(explain(err));
    } finally {
      setBusy(false);
    }
  }

  return (
    <div>
      <PageHeader title="Role Menus" description="Members take roles from a message you publish or one that already exists.">
        <Link href={`${base}/new`} className="inline-flex h-8 items-center bg-accent px-3 text-small text-fg-1">New menu</Link>
      </PageHeader>
      {menus.length === 0 ? (
        <p className="border border-line-subtle px-3 py-6 text-small text-fg-3">Create your first role menu.</p>
      ) : (
        <ul className="divide-y divide-line-subtle border border-line-subtle">
          {menus.map((menu) => {
            const channel = menu.channel_id ? `#${channelNames[menu.channel_id] || "channel"}` : "No channel";
            const excerpt = menu.payload?.embeds?.[0]?.title || menu.payload?.content || menu.name;
            return (
              <li key={menu.id} className="grid gap-2 px-3 py-2 lg:grid-cols-[minmax(0,1fr)_auto] lg:items-center">
                <div className="min-w-0">
                  <p className="truncate text-small text-fg-1">{menu.name}</p>
                  <p className="truncate text-caption text-fg-3">{channel} · {excerpt} · {menuTypeLabel(menu.type)} · {menuModeLabel(menu.mode)} · {menu.options?.length || 0} options · {menu.status}</p>
                  {(menu.warnings || []).slice(0, 1).map((warning: string) => <p key={warning} className="text-caption text-fg-2">{warning}</p>)}
                </div>
                <div className="flex flex-wrap gap-1">
                  <Button type="button" size="sm" variant="secondary" onClick={() => router.push(`${base}/${menu.id}`)}>Edit</Button>
                  <Button type="button" size="sm" variant="ghost" disabled={busy} onClick={() => void run(async () => { const copy = await api.duplicateRoleMenu(guildId, menu.id); router.push(`${base}/${copy.id}`); }, "Draft copy created")}>Duplicate</Button>
                  <Button type="button" size="sm" variant="ghost" disabled={busy} onClick={() => void run(() => api.updateRoleMenu(guildId, menu.id, { enabled: !menu.enabled }), menu.enabled ? "Menu disabled" : "Menu enabled")}>{menu.enabled ? "Disable" : "Enable"}</Button>
                  <Button type="button" size="sm" variant="ghost" disabled={busy} onClick={() => void run(() => api.deleteRoleMenu(guildId, menu.id, false), "Menu deleted")}>Delete</Button>
                  <Button type="button" size="sm" variant="danger-secondary" disabled={busy} onClick={() => void run(() => api.deleteRoleMenu(guildId, menu.id, true), "Menu and reactions removed")}>Clear reactions</Button>
                </div>
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
