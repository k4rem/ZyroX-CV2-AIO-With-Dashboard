import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { isRootOwner } from "@/lib/utils";
import { loadOverview } from "@/lib/loadOverview";
import { OverviewContent } from "@/components/overview/overview-content";

export const revalidate = 0;

export default async function GuildOverviewPage({ params }: { params: { guildId: string } }) {
  const session = await getServerSession(authOptions);
  const userId = session?.user?.id ?? "";
  const isRoot = isRootOwner(userId);

  const data = await loadOverview({
    guildId: params.guildId,
    isRoot,
    userId,
  });

  return <OverviewContent data={data} guildId={params.guildId} />;
}
