import { redirect } from "next/navigation";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import { isRootOwner } from "@/lib/utils";
import { resolvePostAuthDestination } from "@/lib/authRouting";

export const dynamic = "force-dynamic";

/** DS §14 / §16.3 — route to an authorized destination; no legacy home content. */
export default async function DashboardRootPage() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    redirect("/");
  }

  const isRoot = isRootOwner(session.user.id);
  let guildIds: string[] = [];
  try {
    guildIds = (await api.listGuilds()).map((g) => String(g.id));
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      redirect("/?notice=session-ended");
    }
  }

  redirect(resolvePostAuthDestination({ guildIds, isRoot }));
}
