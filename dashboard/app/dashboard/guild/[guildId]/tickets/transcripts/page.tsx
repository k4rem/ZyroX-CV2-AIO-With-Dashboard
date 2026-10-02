import { TranscriptsView } from "@/components/dashboard/tickets/transcripts-view";
import { api } from "@/lib/api";
import { ticketPageData } from "@/lib/ticketPageData";

export default async function TicketTranscriptsPage({ params }: { params: { guildId: string } }) {
  const [rows, context] = await Promise.all([
    api.getTicketTranscripts(params.guildId).catch(() => ({ transcripts: [] })),
    ticketPageData(params.guildId),
  ]);
  return (
    <TranscriptsView
      guildId={params.guildId}
      rows={rows.transcripts || []}
      categories={context.workspace.categories || []}
    />
  );
}
