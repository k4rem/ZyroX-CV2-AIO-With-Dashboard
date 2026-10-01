"use client";

import { useState } from "react";
import { toast } from "sonner";
import { PageHeader } from "@/components/dashboard/page-header";
import { DiscordPreview } from "@/components/discord/discord-preview";
import { ModuleLinks } from "@/components/settings/module-links";
import { SaveBar } from "@/components/settings/save-bar";
import { useDraft } from "@/components/settings/use-draft";
import { api } from "@/lib/api";

export function JoinDmWorkspace({
  guildId,
  initialMessage,
  guildName,
  botName,
  botAvatar,
}: {
  guildId: string;
  initialMessage: string;
  guildName: string | null;
  botName: string;
  botAvatar: string | null;
}) {
  const { draft, setDraft, dirty, reset, commit } = useDraft(initialMessage);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const sent = guildName ? `${draft}\n\nSent from ${guildName}` : draft;

  const save = async () => {
    setSaving(true);
    setError(null);
    try {
      await api.updateJoinDM(guildId, { message: draft });
      commit(draft);
      toast.success("Direct message saved");
    } catch {
      setError("Could not save the direct message.");
      toast.error("Could not save the direct message");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div>
      <PageHeader title="Welcome" description="A private message sent when a member joins. It is stored as written." />
      <ModuleLinks
        label="Welcome"
        links={[
          { href: `/dashboard/guild/${guildId}/welcome`, label: "Channel message" },
          { href: `/dashboard/guild/${guildId}/joindm`, label: "Direct message", current: true },
        ]}
      />
      <div className="grid items-start gap-6 lg:grid-cols-[minmax(280px,480px)_minmax(0,1fr)]">
        <label className="block text-body text-fg-1">
          Message
          <textarea
            value={draft}
            onChange={(event) => setDraft(event.target.value)}
            className="mt-2 min-h-40 w-full rounded-sm border border-line-input bg-surface-well p-2 text-body text-fg-1 outline-none focus-visible:border-brand-400"
          />
          <p className="mt-2 text-small text-fg-3" dir="auto">
            Placeholders are not replaced in direct messages. The bot adds the Sent from line itself.
          </p>
        </label>
        <div className="border border-line-subtle">
          <DiscordPreview
            mode="dm"
            botName={botName}
            botAvatar={botAvatar}
            content={sent}
            warnTokens={[]}
            width="desktop"
            note="This is the message the bot sends. It is not a channel embed."
          />
        </div>
      </div>
      <SaveBar dirty={dirty} saving={saving} error={error} onSave={() => void save()} onDiscard={reset} />
    </div>
  );
}
