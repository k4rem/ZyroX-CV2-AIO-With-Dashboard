import { CategoriesView } from "@/components/dashboard/tickets/categories-view";
import { api } from "@/lib/api";
import { ticketPageData } from "@/lib/ticketPageData";

export default async function TicketCategoriesPage({ params }: { params: { guildId: string } }) {
  const [context, counts] = await Promise.all([
    ticketPageData(params.guildId),
    api.getTicketCategoryCounts(params.guildId).catch(() => ({ counts: {} })),
  ]);
  return (
    <CategoriesView
      guildId={params.guildId}
      categories={context.workspace.categories || []}
      roles={context.roleOptions}
      discordCategories={context.discordCategories}
      counts={counts.counts || {}}
    />
  );
}
