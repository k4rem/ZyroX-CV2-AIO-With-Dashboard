"use client";

import { useEffect, useState } from "react";
import { MoreHorizontal } from "lucide-react";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { ModuleLinks } from "@/components/settings/module-links";
import { SaveBar } from "@/components/settings/save-bar";
import { useDraft } from "@/components/settings/use-draft";
import { Button } from "@/components/ui/button";
import { Combobox, type ComboboxOption } from "@/components/ui/combobox";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { StatusLabel } from "@/components/ui/status";
import { api } from "@/lib/api";
import {
  CUSTOM_ROLE_COMMANDS,
  buildCustomRolesUpdate,
  customRolesDraftFromApi,
  rolePlace,
  roleSwatch,
  type CustomRoleKey,
} from "@/lib/modulePayloads";
import type { DiscordRole } from "@/types/api";

export function CustomRolesWorkspace({
  guildId,
  initialConfig,
  roles,
  prefix,
}: {
  guildId: string;
  initialConfig: Record<string, unknown>;
  roles: DiscordRole[];
  prefix: string;
}) {
  const { draft, setDraft, dirty, reset, commit } = useDraft(customRolesDraftFromApi(initialConfig));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [editing, setEditing] = useState<CustomRoleKey | null>(null);
  const [width, setWidth] = useState(1280);

  useEffect(() => {
    const onResize = () => setWidth(window.innerWidth);
    onResize();
    window.addEventListener("resize", onResize);
    return () => window.removeEventListener("resize", onResize);
  }, []);

  const assignable = roles.filter((role) => role.name !== "@everyone" && !role.managed);
  const options: ComboboxOption[] = assignable.map((role) => {
    const place = rolePlace(role.id, roles);
    return {
      value: role.id,
      label: role.name,
      swatch: roleSwatch(role.color),
      meta: place ? `#${place.rank}` : undefined,
    };
  });
  const assigned = CUSTOM_ROLE_COMMANDS.filter((command) => draft[command.key]).length;
  const compact = width < 768;

  const roleById = (id: string | null) => (id ? roles.find((role) => role.id === id) ?? null : null);

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.updateCustomRoles(guildId, buildCustomRolesUpdate(draft));
      commit(draft);
      toast.success("Custom roles saved");
    } catch (err) {
      const message = err instanceof Error ? err.message : "Could not save custom roles.";
      setError(message);
      toast.error(message);
    } finally {
      setSaving(false);
    }
  };

  const gate = roleById(draft.reqrole);
  const gatePlace = rolePlace(draft.reqrole, roles);
  const ladder = [...CUSTOM_ROLE_COMMANDS.map((command) => roleById(draft[command.key])), gate]
    .filter((role): role is DiscordRole => Boolean(role))
    .sort((a, b) => b.position - a.position);

  return (
    <div>
      <PageHeader title="Roles" description="Prefix commands that add or remove a preset role.">
        {dirty ? <span className="text-small text-fg-2">Unsaved</span> : null}
        <span className="font-mono text-caption text-fg-3">{assigned} of 5 assigned</span>
      </PageHeader>
      <ModuleLinks
        label="Roles"
        links={[
          { href: `/dashboard/guild/${guildId}/customroles`, label: "Custom roles", current: true },
          { href: `/dashboard/guild/${guildId}/invcrole`, label: "Voice role" },
          { href: `/dashboard/guild/${guildId}/vanityroles`, label: "Vanity roles" },
        ]}
      />

      <div className={width >= 1440 ? "grid grid-cols-[minmax(0,1100px)_320px] gap-8" : "max-w-[1100px]"}>
        <div>
          <section aria-labelledby="roles-gate">
            <h2 id="roles-gate" className="cls-overline text-fg-2">
              Gate
            </h2>
            <div className="mt-2 flex flex-wrap items-center justify-between gap-3 border-y border-line py-2">
              <div className="min-w-0">
                <p className="text-body text-fg-1">Who can use these commands</p>
                <p className="text-small text-fg-3">Members without this role cannot run them. Unset: admins only.</p>
              </div>
              <div className="flex items-center gap-3">
                {gate ? (
                  <span className="inline-flex items-center gap-2 text-body text-fg-1">
                    <Dot color={roleSwatch(gate.color)} />
                    {gate.name}
                    {gatePlace ? <span className="font-mono text-caption text-fg-3">#{gatePlace.rank} of {gatePlace.total}</span> : null}
                  </span>
                ) : (
                  <StatusLabel status="disabled">Admins only</StatusLabel>
                )}
                <div className="w-56">
                  <Combobox
                    value={draft.reqrole}
                    onValueChange={(value) => setDraft({ ...draft, reqrole: value })}
                    options={options}
                    placeholder="Change"
                    searchLabel="Search roles"
                  />
                </div>
              </div>
            </div>
          </section>

          <section className="mt-6" aria-labelledby="roles-roster">
            <h2 id="roles-roster" className="cls-overline text-fg-2">
              Roster
            </h2>
            <div className="mt-2 border-t border-line" role="table" aria-label="Custom role commands">
              {!compact ? (
                <div className="grid grid-cols-[9rem_minmax(0,1fr)_7rem_6rem_2rem] gap-3 border-b border-line-subtle py-2 text-caption text-fg-3" role="row">
                  <span>Command</span>
                  <span>Role</span>
                  <span>Position</span>
                  <span>State</span>
                  <span className="sr-only">Actions</span>
                </div>
              ) : null}
              {CUSTOM_ROLE_COMMANDS.map((command) => {
                const role = roleById(draft[command.key]);
                const place = rolePlace(draft[command.key], roles);
                const commandText = `${prefix}${command.name}`;
                return (
                  <div
                    key={command.key}
                    role="row"
                    className="grid items-center gap-2 border-b border-line-subtle py-2 sm:min-h-11 sm:grid-cols-[9rem_minmax(0,1fr)_7rem_6rem_2rem] sm:gap-3"
                  >
                    <span className="font-mono text-body text-fg-1" title="Adds or removes the role for the mentioned member.">
                      {commandText}
                    </span>
                    <div>
                      {editing === command.key ? (
                        <Combobox
                          value={draft[command.key]}
                          onValueChange={(value) => {
                            setDraft({ ...draft, [command.key]: value });
                            setEditing(null);
                          }}
                          options={options}
                          placeholder="Select a role"
                          searchLabel={`Search roles for ${commandText}`}
                        />
                      ) : (
                        <button type="button" className="inline-flex items-center gap-2 text-body text-fg-1" onClick={() => setEditing(command.key)}>
                          <Dot color={role ? roleSwatch(role.color) : null} />
                          {role?.name ?? "Not set"}
                        </button>
                      )}
                    </div>
                    <span className="font-mono text-small tabular-nums text-fg-2">
                      {place ? `#${place.rank} of ${place.total}` : "—"}
                    </span>
                    <StatusLabel status={role ? "online" : "disabled"}>{role ? "Assigned" : "Not set"}</StatusLabel>
                    <DropdownMenu>
                      <DropdownMenuTrigger asChild>
                        <Button type="button" variant="ghost" size="icon-sm" aria-label={`Edit ${commandText}`}>
                          <MoreHorizontal className="size-4" aria-hidden="true" />
                        </Button>
                      </DropdownMenuTrigger>
                      <DropdownMenuContent>
                        <DropdownMenuItem onSelect={() => setEditing(command.key)}>Change role</DropdownMenuItem>
                        <DropdownMenuItem onSelect={() => setDraft({ ...draft, [command.key]: null })}>Clear</DropdownMenuItem>
                      </DropdownMenuContent>
                    </DropdownMenu>
                  </div>
                );
              })}
            </div>
            <p className="mt-3 text-small text-fg-3">The bot&apos;s role must be above every assigned role to hand them out.</p>
          </section>
        </div>

        {ladder.length > 0 ? (
          <aside className={width >= 1440 ? "" : "mt-6 max-w-sm"}>
            <h2 className="cls-overline text-fg-2">Role ladder</h2>
            <ol className="mt-2 border border-line">
              {ladder.map((role) => (
                <li key={role.id} className="flex items-center gap-2 border-b border-line-subtle px-2 py-1.5 last:border-b-0">
                  <Dot color={roleSwatch(role.color)} />
                  <span className="min-w-0 flex-1 truncate text-body text-fg-1">{role.name}</span>
                  <span className="font-mono text-caption text-fg-3">
                    {rolePlace(role.id, roles) ? `#${rolePlace(role.id, roles)?.rank}` : "—"}
                  </span>
                </li>
              ))}
            </ol>
          </aside>
        ) : null}
      </div>

      <SaveBar dirty={dirty} saving={saving} error={error} onSave={() => void save()} onDiscard={() => { reset(); setEditing(null); }} />
    </div>
  );
}

function Dot({ color }: { color: string | null }) {
  if (!color) return <span aria-hidden="true" className="size-2.5 shrink-0 rounded-full border border-fg-3" />;
  return <span aria-hidden="true" className="size-2.5 shrink-0 rounded-full" style={{ backgroundColor: color }} />;
}
