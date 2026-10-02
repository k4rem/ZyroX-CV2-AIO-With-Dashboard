"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { PageHeader } from "@/components/dashboard/page-header";
import { TicketsNav } from "@/components/dashboard/tickets/tickets-nav";
import { RolePicker } from "@/components/discord/channel-picker";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";

function explain(err: unknown) {
  return err instanceof Error ? err.message : "The team did not save.";
}

export function CategoriesView({
  guildId,
  categories,
  roles,
  discordCategories,
  counts,
}: {
  guildId: string;
  categories: Array<Record<string, any>>;
  roles: Array<{ id: string; name: string }>;
  discordCategories: Array<{ id: string; name: string }>;
  counts: Record<string, { open: number; total: number }>;
}) {
  const router = useRouter();
  const [name, setName] = useState("Billing");
  const [discordCategory, setDiscordCategory] = useState("");
  const [staff, setStaff] = useState<string[]>([]);
  const [staffPick, setStaffPick] = useState("");
  const [editing, setEditing] = useState<string | null>(null);
  const [draft, setDraft] = useState<Record<string, any>>({});

  async function createCategory() {
    try {
      await api.createTicketCategory(guildId, {
        name,
        discord_category_id: discordCategory || null,
        staff_role_ids: staff,
        ping_staff: true,
        name_format: "ticket-{number}-{username}",
      });
      toast.success("Team saved");
      setName("");
      router.refresh();
    } catch (err) {
      toast.error(explain(err));
    }
  }

  function begin(category: Record<string, any>) {
    setEditing(category.id);
    setDraft({
      name: category.name,
      discord_category_id: category.discord_category_id || "",
      staff_role_ids: category.staff_role_ids || [],
      ping_staff: category.ping_staff !== false,
      name_format: category.name_format || "ticket-{number}-{username}",
      required_role_ids: category.required_role_ids || [],
      blocked_role_ids: category.blocked_role_ids || [],
    });
  }

  async function save() {
    if (!editing) return;
    try {
      await api.updateTicketCategory(guildId, editing, {
        ...draft,
        discord_category_id: draft.discord_category_id || null,
        clear_discord_category: !draft.discord_category_id,
      });
      toast.success("Team updated");
      setEditing(null);
      router.refresh();
    } catch (err) {
      toast.error(explain(err));
    }
  }

  return (
    <div>
      <TicketsNav guildId={guildId} />
      <PageHeader title="Categories & Teams" description="A team is who can see and answer a ticket." />
      <div className="mb-4 grid gap-2 border border-line-subtle p-3 sm:grid-cols-[minmax(0,1fr)_minmax(0,1fr)_auto]">
        <Input value={name} onChange={(event) => setName(event.target.value)} aria-label="Team name" placeholder="Team name" />
        <Select value={discordCategory} onValueChange={setDiscordCategory} placeholder="Discord category" options={discordCategories.map((item) => ({ value: item.id, label: item.name }))} />
        <Button type="button" onClick={() => void createCategory()}>Add team</Button>
        <div className="sm:col-span-3">
          <p className="mb-1 text-caption text-fg-3">Support roles</p>
          <RolePicker roles={roles} value={staffPick} onChange={(id) => { setStaffPick(id); setStaff((current) => current.includes(id) ? current : [...current, id]); }} />
          <p className="mt-1 text-caption text-fg-3">{staff.map((id) => roles.find((role) => role.id === id)?.name || "Role").join(", ") || "No support roles yet."}</p>
        </div>
      </div>
      {categories.length === 0 ? (
        <p className="text-small text-fg-3">No teams yet.</p>
      ) : (
        <ul className="divide-y divide-line-subtle border border-line-subtle">
          {categories.map((category) => {
            const count = counts[category.id] || { open: 0, total: 0 };
            const support = (category.staff_role_ids || []).map((id: string) => roles.find((role) => role.id === id)?.name || "Role").join(", ") || "No support roles";
            const parent = discordCategories.find((item) => item.id === category.discord_category_id)?.name || "No Discord category";
            const open = editing === category.id;
            return (
              <li key={category.id} className="px-3 py-2">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-small text-fg-1">{category.name}</p>
                    <p className="text-caption text-fg-3">{parent} · {support} · {count.open} open / {count.total} total · {category.ping_staff === false ? "No open ping" : "Pings support on open"}</p>
                  </div>
                  <Button type="button" size="sm" variant="secondary" onClick={() => open ? setEditing(null) : begin(category)}>{open ? "Close" : "Edit"}</Button>
                </div>
                {open && (
                  <div className="mt-2 grid gap-2">
                    <Input value={draft.name || ""} aria-label="Team name" onChange={(event) => setDraft({ ...draft, name: event.target.value })} />
                    <Select value={draft.discord_category_id || ""} onValueChange={(value) => setDraft({ ...draft, discord_category_id: value })} placeholder="Discord category" options={discordCategories.map((item) => ({ value: item.id, label: item.name }))} />
                    <RolePicker roles={roles} value="" onChange={(id) => setDraft({ ...draft, staff_role_ids: Array.from(new Set([...(draft.staff_role_ids || []), id])) })} />
                    <p className="text-caption text-fg-3">{(draft.staff_role_ids || []).map((id: string) => roles.find((role) => role.id === id)?.name || "Role").join(", ")}</p>
                    <Input value={draft.name_format || ""} aria-label="Channel name pattern" onChange={(event) => setDraft({ ...draft, name_format: event.target.value })} />
                    <p className="text-caption text-fg-3">Use {"{number}"} and {"{username}"}. The bot must sit above support roles to manage the channel.</p>
                    <label className="flex items-center gap-2 text-small text-fg-2">
                      <input type="checkbox" checked={draft.ping_staff !== false} onChange={(event) => setDraft({ ...draft, ping_staff: event.target.checked })} />
                      Ping support roles when a ticket opens
                    </label>
                    <p className="text-caption text-fg-3">Required role for this team</p>
                    <RolePicker roles={roles} value={(draft.required_role_ids || [])[0] || ""} onChange={(id) => setDraft({ ...draft, required_role_ids: [id] })} />
                    <p className="text-caption text-fg-3">Blocked role for this team</p>
                    <RolePicker roles={roles} value={(draft.blocked_role_ids || [])[0] || ""} onChange={(id) => setDraft({ ...draft, blocked_role_ids: [id] })} />
                    <Button type="button" onClick={() => void save()}>Save team</Button>
                  </div>
                )}
              </li>
            );
          })}
        </ul>
      )}
    </div>
  );
}
