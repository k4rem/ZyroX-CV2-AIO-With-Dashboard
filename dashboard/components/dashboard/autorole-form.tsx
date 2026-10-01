"use client";

import { useMemo, useState } from "react";
import { toast } from "sonner";
import { SaveBar } from "@/components/settings/save-bar";
import { SettingGroup } from "@/components/settings/setting-group";
import { SettingsInstrument } from "@/components/settings/settings-instrument";
import { Button } from "@/components/ui/button";
import { Combobox } from "@/components/ui/combobox";
import { api } from "@/lib/api";
import { draftsDiffer, roleSwatch } from "@/lib/modulePayloads";
import type { AutoRoleConfig, DiscordRole } from "@/types/api";

const LIMIT = 10;

export function AutoRoleForm({
  initialConfig,
  roles,
  guildId,
}: {
  initialConfig: AutoRoleConfig;
  roles: DiscordRole[];
  guildId: string;
}) {
  const [saved, setSaved] = useState({ humans: initialConfig.humans, bots: initialConfig.bots });
  const [draft, setDraft] = useState({ humans: initialConfig.humans, bots: initialConfig.bots });
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const dirty = draftsDiffer(saved, draft);

  const assignable = useMemo(
    () =>
      roles
        .filter((role) => role.name !== "@everyone" && !role.managed)
        .sort((a, b) => (b.position ?? 0) - (a.position ?? 0)),
    [roles],
  );

  const addRole = (type: "humans" | "bots", roleId: string | null) => {
    if (!roleId || draft[type].includes(roleId)) return;
    if (draft[type].length >= LIMIT) {
      toast.error(`Up to ${LIMIT} roles for ${type === "humans" ? "members" : "bots"}.`);
      return;
    }
    setDraft({ ...draft, [type]: [...draft[type], roleId] });
  };

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.updateAutoRole(guildId, { humans: draft.humans, bots: draft.bots });
      setSaved(draft);
      toast.success("Auto roles saved");
    } catch {
      setError("Could not save auto roles.");
      toast.error("Could not save auto roles");
    } finally {
      setSaving(false);
    }
  };

  const renderList = (type: "humans" | "bots", label: string, description: string) => (
    <SettingGroup id={`autorole-${type}`} label={label} meta={`${draft[type].length} of ${LIMIT}`}>
      <p className="mt-1 text-small text-fg-3" dir="auto">{description}</p>
      <ul className="mt-2 border-t border-line">
        {draft[type].length === 0 ? (
          <li className="py-3 text-small text-fg-3">None assigned.</li>
        ) : (
          draft[type].map((roleId) => {
            const role = roles.find((item) => item.id === roleId);
            return (
              <li key={roleId} className="flex items-center justify-between gap-3 border-b border-line-subtle py-2">
                <span className="inline-flex min-w-0 items-center gap-2 text-body text-fg-1">
                  <span
                    className="size-2.5 shrink-0 rounded-full border border-line"
                    style={{ background: roleSwatch(role?.color) ?? "transparent" }}
                  />
                  <span className="truncate">{role?.name ?? roleId}</span>
                </span>
                <Button
                  type="button"
                  variant="ghost"
                  size="sm"
                  onClick={() => setDraft({ ...draft, [type]: draft[type].filter((id) => id !== roleId) })}
                >
                  Remove
                </Button>
              </li>
            );
          })
        )}
      </ul>
      <div className="mt-3 max-w-sm">
        <Combobox
          value={null}
          onValueChange={(value) => addRole(type, value)}
          options={assignable
            .filter((role) => !draft[type].includes(role.id))
            .map((role) => ({ value: role.id, label: role.name, swatch: roleSwatch(role.color) }))}
          placeholder={type === "humans" ? "Add a member role" : "Add a bot role"}
          searchLabel="Search roles"
        />
      </div>
    </SettingGroup>
  );

  return (
    <SettingsInstrument
      summary={`${draft.humans.length} member roles · ${draft.bots.length} bot roles. Up to ${LIMIT} each. The bot role must sit above them.`}
    >
      {renderList("humans", "Members", "Roles given when a person joins.")}
      {renderList("bots", "Bots", "Roles given when a bot joins.")}
      <SaveBar
        dirty={dirty}
        saving={saving}
        error={error}
        onSave={() => void save()}
        onDiscard={() => {
          setDraft(saved);
          setError(null);
        }}
      />
    </SettingsInstrument>
  );
}
