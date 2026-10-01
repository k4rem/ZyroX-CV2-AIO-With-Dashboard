import React from "react";
import { MessagesWorkspace } from "@/components/dashboard/messages-workspace";
import { api } from "@/lib/api";

export default async function MessagesPage({
  params,
  searchParams,
}: {
  params: { guildId: string };
  searchParams?: { tab?: string };
}) {
  const [templates, sent, channels, emojis, context] = await Promise.all([
    api.listMessageTemplates(params.guildId).catch(() => ({ templates: [] })),
    api.listSentMessages(params.guildId).catch(() => ({ sent: [] })),
    api.getChannels(params.guildId).catch(() => []),
    api.listGuildEmojis(params.guildId).catch(() => ({ emojis: [] })),
    api.messageContext(params.guildId).catch(() => ({ variables: [] })),
  ]);
  const values = Object.fromEntries((context.variables || []).map((item: { id: string; value: string }) => [item.id, item.value]));
  return (
    <MessagesWorkspace
      guildId={params.guildId}
      templates={templates.templates || []}
      sent={sent.sent || []}
      channels={Array.isArray(channels) ? channels : []}
      emojis={emojis.emojis || []}
      values={values}
      initialTab={searchParams?.tab}
    />
  );
}
