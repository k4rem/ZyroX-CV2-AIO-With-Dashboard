"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { RolePicker } from "@/components/discord/channel-picker";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Select } from "@/components/ui/select";

type RoleOption = { id: string; name: string };
type Condition = { kind: string; role_id?: string; op?: string; amount?: number; unit?: string };
type Rule = {
  id: string;
  name: string;
  trigger: string;
  trigger_role_id?: string | null;
  conditions: Condition[];
  action: string;
  action_role_id: string;
  delay_seconds: number;
  enabled: boolean;
  warnings?: string[];
  status?: string;
  matches?: number | null;
};

const TRIGGERS = [
  { value: "join", label: "Member joins" },
  { value: "screening", label: "Membership screening completed" },
  { value: "role_add", label: "Member gains a role" },
  { value: "role_remove", label: "Member loses a role" },
];
const CONDITIONS = [
  { value: "human", label: "Member is human" },
  { value: "bot", label: "Member is a bot" },
  { value: "has_role", label: "Has role" },
  { value: "lacks_role", label: "Does not have role" },
  { value: "account_age", label: "Account age" },
];
const ACTIONS = [
  { value: "add", label: "Add role" },
  { value: "remove", label: "Remove role" },
];
const JOIN_DELAYS = [
  { value: "0", label: "Immediately" },
  { value: "10", label: "10 seconds" },
  { value: "60", label: "1 minute" },
  { value: "300", label: "5 minutes" },
  { value: "custom", label: "Custom duration" },
];
const RULE_DELAYS = [
  { value: "0", label: "Immediately" },
  { value: "30", label: "30 seconds" },
  { value: "300", label: "5 minutes" },
  { value: "custom", label: "Custom" },
];

function explain(err: unknown) {
  return err instanceof Error ? err.message : "That did not save.";
}

function delayChoice(seconds: number, presets: { value: string }[]) {
  const known = presets.some((item) => item.value === String(seconds));
  return known ? String(seconds) : "custom";
}

function roleName(roles: RoleOption[], id?: string | null) {
  if (!id) return "a role";
  return roles.find((role) => role.id === id)?.name || "Missing role";
}

function summary(rule: Rule, roles: RoleOption[]) {
  const trigger = TRIGGERS.find((item) => item.value === rule.trigger)?.label || "When";
  const roleBit = rule.trigger === "role_add" || rule.trigger === "role_remove" ? ` @${roleName(roles, rule.trigger_role_id)}` : "";
  const conditions = rule.conditions.length
    ? rule.conditions.map((item) => {
        if (item.kind === "has_role" || item.kind === "lacks_role") return `${item.kind === "has_role" ? "Has" : "Lacks"} @${roleName(roles, item.role_id)}`;
        if (item.kind === "account_age") return `Account age ${item.op === "gt" ? "over" : "at least"} ${item.amount || 0} ${item.unit || "days"}`;
        return CONDITIONS.find((kind) => kind.value === item.kind)?.label || item.kind;
      }).join(", ")
    : "Anyone";
  const action = `${rule.action === "remove" ? "Remove" : "Add"} @${roleName(roles, rule.action_role_id)}`;
  return { trigger: `${trigger}${roleBit}`, conditions, action };
}

export function RoleAutomation({
  guildId,
  join,
  rules,
  roles,
}: {
  guildId: string;
  join: { member_role_ids: string[]; bot_role_ids: string[]; delay_seconds: number; screening: string };
  rules: Rule[];
  roles: RoleOption[];
}) {
  const router = useRouter();
  const [view, setView] = useState<"join" | "rules">("join");
  const [members, setMembers] = useState(join.member_role_ids || []);
  const [bots, setBots] = useState(join.bot_role_ids || []);
  const [delay, setDelay] = useState(delayChoice(join.delay_seconds || 0, JOIN_DELAYS));
  const [customDelay, setCustomDelay] = useState(String(join.delay_seconds || 60));
  const [screening, setScreening] = useState(join.screening || "immediate");
  const [draft, setDraft] = useState<Rule | null>(null);
  const [busy, setBusy] = useState(false);

  async function saveJoin() {
    setBusy(true);
    try {
      await api.saveJoinRoles(guildId, {
        member_role_ids: members,
        bot_role_ids: bots,
        delay_seconds: delay === "custom" ? Number(customDelay) || 0 : Number(delay),
        screening,
      });
      toast.success("Join roles saved");
      router.refresh();
    } catch (err) {
      toast.error(explain(err));
    } finally {
      setBusy(false);
    }
  }

  async function saveRule() {
    if (!draft?.action_role_id) {
      toast.error("Choose the role this rule changes.");
      return;
    }
    setBusy(true);
    const body = {
      name: draft.name,
      trigger: draft.trigger,
      trigger_role_id: draft.trigger === "role_add" || draft.trigger === "role_remove" ? draft.trigger_role_id : null,
      conditions: draft.conditions,
      action: draft.action,
      action_role_id: draft.action_role_id,
      delay_seconds: draft.delay_seconds,
      enabled: draft.enabled,
    };
    try {
      if (draft.id) await api.updateRoleRule(guildId, draft.id, body);
      else await api.createRoleRule(guildId, body);
      setDraft(null);
      toast.success("Rule saved");
      router.refresh();
    } catch (err) {
      toast.error(explain(err));
    } finally {
      setBusy(false);
    }
  }

  async function act(action: "duplicate" | "delete" | "toggle", rule: Rule) {
    setBusy(true);
    try {
      if (action === "duplicate") await api.duplicateRoleRule(guildId, rule.id);
      else if (action === "delete") await api.deleteRoleRule(guildId, rule.id);
      else await api.updateRoleRule(guildId, rule.id, { enabled: !rule.enabled });
      router.refresh();
    } catch (err) {
      toast.error(explain(err));
    } finally {
      setBusy(false);
    }
  }

  function blank(): Rule {
    return { id: "", name: "New rule", trigger: "role_add", trigger_role_id: "", conditions: [{ kind: "human" }], action: "add", action_role_id: "", delay_seconds: 0, enabled: true };
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <Button type="button" variant={view === "join" ? "default" : "secondary"} onClick={() => setView("join")}>Join Roles</Button>
        <Button type="button" variant={view === "rules" ? "default" : "secondary"} onClick={() => setView("rules")}>Automation Rules</Button>
      </div>

      {view === "join" ? (
        <section className="space-y-4 rounded-md border border-line bg-surface-1 p-4">
          <RoleList label="Member join roles" roles={roles} selected={members} onAdd={(id) => id && setMembers((current) => current.includes(id) ? current : [...current, id])} onRemove={(id) => setMembers((current) => current.filter((item) => item !== id))} />
          <RoleList label="Bot join roles" roles={roles} selected={bots} onAdd={(id) => id && setBots((current) => current.includes(id) ? current : [...current, id])} onRemove={(id) => setBots((current) => current.filter((item) => item !== id))} />
          <div className="grid gap-3 sm:grid-cols-2">
            <label className="space-y-1 text-sm">
              <span className="text-muted">Delay</span>
              <Select value={delay} onValueChange={setDelay} options={JOIN_DELAYS} />
            </label>
            <label className="space-y-1 text-sm">
              <span className="text-muted">Screening</span>
              <Select value={screening} onValueChange={setScreening} options={[{ value: "immediate", label: "Assign immediately" }, { value: "screening", label: "Wait until member passes screening" }]} />
            </label>
          </div>
          {delay === "custom" ? <Input value={customDelay} onChange={(event) => setCustomDelay(event.target.value.replace(/[^\d]/g, ""))} placeholder="Seconds" /> : null}
          <Button type="button" onClick={saveJoin} disabled={busy}>Save join roles</Button>
        </section>
      ) : (
        <section className="space-y-3">
          <div className="flex justify-end">
            <Button type="button" onClick={() => setDraft(blank())}>New rule</Button>
          </div>
          {rules.map((rule) => {
            const text = summary(rule, roles);
            return (
              <article key={rule.id} className="space-y-2 rounded-md border border-line bg-surface-1 p-3">
                <div className="flex flex-wrap items-center justify-between gap-2">
                  <h3 className="text-sm font-medium">{rule.name}</h3>
                  <span className="text-xs text-muted">{rule.status}</span>
                </div>
                <p className="text-sm text-muted">When {text.trigger}</p>
                <p className="text-sm text-muted">If {text.conditions}</p>
                <p className="text-sm text-muted">Then {text.action}{rule.delay_seconds ? ` after ${rule.delay_seconds}s` : ""}</p>
                {typeof rule.matches === "number" ? <p className="text-xs text-muted">Currently matches {rule.matches} members</p> : null}
                {(rule.warnings || []).map((warning) => <p key={warning} className="text-xs text-amber-300">{warning}</p>)}
                <div className="flex flex-wrap gap-2">
                  <Button type="button" variant="secondary" onClick={() => setDraft(rule)}>Edit</Button>
                  <Button type="button" variant="secondary" onClick={() => act("duplicate", rule)} disabled={busy}>Duplicate</Button>
                  <Button type="button" variant="secondary" onClick={() => act("toggle", rule)} disabled={busy}>{rule.enabled ? "Disable" : "Enable"}</Button>
                  <Button type="button" variant="danger-secondary" onClick={() => act("delete", rule)} disabled={busy}>Delete</Button>
                </div>
              </article>
            );
          })}
          {!rules.length ? <p className="text-sm text-muted">No automation rules yet.</p> : null}
        </section>
      )}

      {draft ? (
        <section className="space-y-3 rounded-md border border-line bg-surface-1 p-4">
          <Input value={draft.name} onChange={(event) => setDraft({ ...draft, name: event.target.value })} placeholder="Rule name" />
          <div className="grid gap-2 sm:grid-cols-[5rem_1fr]">
            <span className="pt-2 text-xs uppercase tracking-wide text-muted">When</span>
            <div className="grid gap-2 sm:grid-cols-2">
              <Select value={draft.trigger} onValueChange={(value) => setDraft({ ...draft, trigger: value })} options={TRIGGERS} />
              {draft.trigger === "role_add" || draft.trigger === "role_remove" ? <RolePicker roles={roles} value={draft.trigger_role_id || ""} onChange={(id) => setDraft({ ...draft, trigger_role_id: id })} /> : null}
            </div>
            <span className="pt-2 text-xs uppercase tracking-wide text-muted">If</span>
            <div className="space-y-2">
              {draft.conditions.map((condition, index) => (
                <div key={`${condition.kind}-${index}`} className="grid gap-2 sm:grid-cols-[1fr_1fr_auto]">
                  <Select value={condition.kind} onValueChange={(value) => setDraft({ ...draft, conditions: draft.conditions.map((item, itemIndex) => itemIndex === index ? { kind: value, role_id: "", op: "gte", amount: 1, unit: "days" } : item) })} options={CONDITIONS} />
                  {condition.kind === "has_role" || condition.kind === "lacks_role" ? <RolePicker roles={roles} value={condition.role_id || ""} onChange={(id) => setDraft({ ...draft, conditions: draft.conditions.map((item, itemIndex) => itemIndex === index ? { ...item, role_id: id } : item) })} /> : null}
                  {condition.kind === "account_age" ? (
                    <>
                      <Select value={condition.op || "gte"} onValueChange={(value) => setDraft({ ...draft, conditions: draft.conditions.map((item, itemIndex) => itemIndex === index ? { ...item, op: value } : item) })} options={[{ value: "gte", label: "At least" }, { value: "gt", label: "Greater than" }]} />
                      <Input value={String(condition.amount || 1)} onChange={(event) => setDraft({ ...draft, conditions: draft.conditions.map((item, itemIndex) => itemIndex === index ? { ...item, amount: Number(event.target.value) || 0 } : item) })} />
                      <Select value={condition.unit || "days"} onValueChange={(value) => setDraft({ ...draft, conditions: draft.conditions.map((item, itemIndex) => itemIndex === index ? { ...item, unit: value } : item) })} options={[{ value: "hours", label: "Hours" }, { value: "days", label: "Days" }]} />
                    </>
                  ) : null}
                  <Button type="button" variant="secondary" onClick={() => setDraft({ ...draft, conditions: draft.conditions.filter((_, itemIndex) => itemIndex !== index) })}>Remove</Button>
                </div>
              ))}
              <Button type="button" variant="secondary" onClick={() => setDraft({ ...draft, conditions: [...draft.conditions, { kind: "human" }] })}>Add condition</Button>
              <p className="text-xs text-muted">All conditions must match.</p>
            </div>
            <span className="pt-2 text-xs uppercase tracking-wide text-muted">Then</span>
            <div className="grid gap-2 sm:grid-cols-2">
              <Select value={draft.action} onValueChange={(value) => setDraft({ ...draft, action: value })} options={ACTIONS} />
              <RolePicker roles={roles} value={draft.action_role_id} onChange={(id) => setDraft({ ...draft, action_role_id: id })} />
            </div>
            <span className="pt-2 text-xs uppercase tracking-wide text-muted">After</span>
            <Select
              value={delayChoice(draft.delay_seconds, RULE_DELAYS)}
              onValueChange={(value) => setDraft({ ...draft, delay_seconds: value === "custom" ? 15 : Number(value) })}
              options={RULE_DELAYS}
            />
          </div>
          {delayChoice(draft.delay_seconds, RULE_DELAYS) === "custom" ? <Input value={String(draft.delay_seconds)} onChange={(event) => setDraft({ ...draft, delay_seconds: Number(event.target.value.replace(/[^\d]/g, "")) || 0 })} placeholder="Seconds" /> : null}
          <div className="flex gap-2">
            <Button type="button" onClick={saveRule} disabled={busy}>Save rule</Button>
            <Button type="button" variant="secondary" onClick={() => setDraft(null)}>Close</Button>
          </div>
        </section>
      ) : null}
    </div>
  );
}

function RoleList({
  label,
  roles,
  selected,
  onAdd,
  onRemove,
}: {
  label: string;
  roles: RoleOption[];
  selected: string[];
  onAdd: (id: string) => void;
  onRemove: (id: string) => void;
}) {
  const [addValue, setAddValue] = useState("");
  return (
    <div className="space-y-2">
      <p className="text-sm">{label}</p>
      <div className="flex flex-wrap gap-2">
        {selected.map((id) => (
          <button key={id} type="button" className="rounded-md border border-line px-2 py-1 text-sm" onClick={() => onRemove(id)}>
            @{roleName(roles, id)} ×
          </button>
        ))}
        {!selected.length ? <span className="text-sm text-muted">None</span> : null}
      </div>
      <div className="grid gap-2 sm:grid-cols-[1fr_auto]">
        <RolePicker roles={roles.filter((role) => !selected.includes(role.id))} value={addValue} onChange={setAddValue} />
        <Button type="button" variant="secondary" onClick={() => { if (!addValue) return; onAdd(addValue); setAddValue(""); }}>Add</Button>
      </div>
    </div>
  );
}
