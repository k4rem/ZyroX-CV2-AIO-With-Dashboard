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
      close_mode: category.close_mode || "direct",
      close_timeout_minutes: category.close_timeout_minutes ?? "",
      hours_mode: category.hours_mode || "always",
      hours_timezone: category.hours_timezone || "UTC",
      hours_days: category.hours_days ?? 127,
      hours_start: category.hours_start || "09:00",
      hours_end: category.hours_end || "17:00",
      hours_outside: category.hours_outside || "allow",
    });
  }

  async function save() {
    if (!editing) return;
    try {
      await api.updateTicketCategory(guildId, editing, {
        ...draft,
        discord_category_id: draft.discord_category_id || null,
        clear_discord_category: !draft.discord_category_id,
        close_timeout_minutes: draft.close_timeout_minutes === "" || draft.close_timeout_minutes == null ? null : Number(draft.close_timeout_minutes),
        clear_close_timeout: draft.close_timeout_minutes === "" || draft.close_timeout_minutes == null,
        hours_days: Number(draft.hours_days ?? 127),
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
                    <p className="text-caption text-fg-3">{parent} · {support} · {count.open} open / {count.total} total · {category.hours_mode === "scheduled" ? (category.support_open ? "Open now" : "Closed now") : "Always available"}{category.support_next && !category.support_open ? ` · Next ${new Date(category.support_next).toLocaleString()}` : ""}</p>
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
                    <Select value={draft.close_mode || "direct"} onValueChange={(value) => setDraft({ ...draft, close_mode: value })} options={[{ value: "direct", label: "Direct close" }, { value: "request", label: "Ask the member to confirm" }]} />
                    <Input value={draft.close_timeout_minutes ?? ""} aria-label="Close request timeout minutes" placeholder="Timeout minutes, blank for no automatic close" onChange={(event) => setDraft({ ...draft, close_timeout_minutes: event.target.value, clear_close_timeout: event.target.value === "" })} />
                    <Select value={draft.hours_mode || "always"} onValueChange={(value) => setDraft({ ...draft, hours_mode: value })} options={[{ value: "always", label: "Always available" }, { value: "scheduled", label: "Scheduled hours" }]} />
                    {draft.hours_mode === "scheduled" && (
                      <div className="grid gap-1 sm:grid-cols-2">
                        <Input value={draft.hours_timezone || "UTC"} aria-label="Timezone" placeholder="Asia/Riyadh" onChange={(event) => setDraft({ ...draft, hours_timezone: event.target.value })} />
                        <Input value={draft.hours_start || ""} aria-label="Opens" placeholder="09:00" onChange={(event) => setDraft({ ...draft, hours_start: event.target.value })} />
                        <Input value={draft.hours_end || ""} aria-label="Closes" placeholder="17:00" onChange={(event) => setDraft({ ...draft, hours_end: event.target.value })} />
                        <Select value={draft.hours_outside || "allow"} onValueChange={(value) => setDraft({ ...draft, hours_outside: value })} options={[{ value: "allow", label: "Allow with offline notice" }, { value: "block", label: "Block new tickets" }]} />
                        <div className="flex flex-wrap gap-1 sm:col-span-2">
                          {["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"].map((day, index) => {
                            const bit = 1 << index;
                            const on = (Number(draft.hours_days) & bit) !== 0;
                            return <button key={day} type="button" className={`border px-2 py-0.5 text-caption ${on ? "border-line text-fg-1" : "border-line-subtle text-fg-3"}`} onClick={() => setDraft({ ...draft, hours_days: Number(draft.hours_days) ^ bit })}>{day}</button>;
                          })}
                        </div>
                      </div>
                    )}
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
