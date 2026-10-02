import Link from "next/link";
import { notFound } from "next/navigation";
import { Conversation } from "@/components/dashboard/tickets/ticket-detail";
import { TicketsNav } from "@/components/dashboard/tickets/tickets-nav";
import { api } from "@/lib/api";
import { eventLabel, ticketStatusLabel } from "@/lib/ticketsModel";

export default async function TranscriptPage({ params }: { params: { guildId: string; ticketId: string } }) {
  const [detail, stored] = await Promise.all([
    api.getTicketDetail(params.guildId, params.ticketId).catch(() => null),
    api.getTicketTranscript(params.guildId, params.ticketId).catch(() => null),
  ]);
  if (!detail) notFound();
  const html = typeof stored?.html === "string" ? stored.html : "";
  return (
    <div>
      <TicketsNav guildId={params.guildId} />
      <p className="text-body text-fg-1">Ticket {String(detail.number).padStart(4, "0")}</p>
      <p className="mb-4 text-small text-fg-3">
        {detail.opener_name || "Member"} · {detail.category_name || "Team"} · {ticketStatusLabel(detail.status)}
        {detail.close_reason ? ` · ${detail.close_reason}` : ""}
      </p>
      <div className="grid gap-4 lg:grid-cols-[minmax(0,1fr)_16rem]">
        <section className="border border-line-subtle p-3">
          <Conversation messages={detail.messages || []} />
        </section>
        <aside className="space-y-2 text-small text-fg-2">
          <p className="text-caption uppercase tracking-wide text-fg-3">Timeline</p>
          {(detail.events || []).map((event: { id: string; kind?: string; actor_name?: string; payload?: Record<string, unknown> }) => <p key={event.id}>{eventLabel(event)}</p>)}
          {html && (
            <a className="inline-block text-accent" href={`data:text/html;charset=utf-8,${encodeURIComponent(html)}`} download={`ticket-${detail.number}.html`}>Download</a>
          )}
          <Link href={`/dashboard/guild/${params.guildId}/tickets/transcripts`} className="block text-fg-3">Back to transcripts</Link>
        </aside>
      </div>
      {html && (
        <iframe title="Full transcript" sandbox="" srcDoc={html} className="mt-4 h-[32rem] w-full border border-line-subtle bg-surface-1" />
      )}
    </div>
  );
}
