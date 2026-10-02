import { QueueView } from "@/components/dashboard/tickets/queue-view";
import { api } from "@/lib/api";
import { ticketPageData } from "@/lib/ticketPageData";

export default async function TicketsQueuePage({ params }: { params: { guildId: string } }) {
  const [queue, context] = await Promise.all([
    api.getTicketQueue(params.guildId).catch(() => ({ tickets: [] })),
    ticketPageData(params.guildId),
  ]);
  return (
    <QueueView
      guildId={params.guildId}
      initial={queue.tickets || []}
      categories={(context.workspace.categories || []).map((category: { id: string; name: string }) => ({ id: category.id, name: category.name }))}
    />
  );
}
