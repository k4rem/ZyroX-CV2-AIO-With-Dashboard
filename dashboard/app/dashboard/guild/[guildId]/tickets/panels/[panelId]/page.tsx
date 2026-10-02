import { notFound } from "next/navigation";
import { PanelBuilder } from "@/components/dashboard/tickets/panel-builder";
import { api } from "@/lib/api";
import { ticketPageData } from "@/lib/ticketPageData";

export default async function TicketPanelPage({ params }: { params: { guildId: string; panelId: string } }) {
  const [panel, context] = await Promise.all([
    api.getTicketPanel(params.guildId, params.panelId).catch(() => null),
    ticketPageData(params.guildId),
  ]);
  if (!panel) notFound();
  return (
    <PanelBuilder
      guildId={params.guildId}
      panel={panel}
      categories={context.workspace.categories || []}
      roles={context.roleOptions}
      channels={context.textChannels}
      emojis={context.emojis}
    />
  );
}
