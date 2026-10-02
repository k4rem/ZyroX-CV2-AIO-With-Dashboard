import { SettingsView } from "@/components/dashboard/tickets/settings-view";
import { api } from "@/lib/api";
import { ticketPageData } from "@/lib/ticketPageData";

export default async function TicketSettingsPage({ params }: { params: { guildId: string } }) {
  const [context, blocked] = await Promise.all([
    ticketPageData(params.guildId),
    api.getTicketBlocklist(params.guildId).catch(() => ({ blocked: [] })),
  ]);
  return (
    <SettingsView
      guildId={params.guildId}
      settings={context.workspace}
      channels={context.textChannels}
      blocked={blocked.blocked || []}
    />
  );
}
