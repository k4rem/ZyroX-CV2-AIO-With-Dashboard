import { PanelsView } from "@/components/dashboard/tickets/panels-view";
import { ticketPageData } from "@/lib/ticketPageData";

export default async function TicketPanelsPage({ params }: { params: { guildId: string } }) {
  const context = await ticketPageData(params.guildId);
  return (
    <PanelsView
      guildId={params.guildId}
      panels={context.workspace.panels || []}
      categories={context.workspace.categories || []}
      channelNames={context.channelNames}
    />
  );
}
