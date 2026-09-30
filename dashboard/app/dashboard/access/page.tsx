import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { authOptions } from "@/lib/auth";
import { isRootOwner } from "@/lib/utils";
import { api } from "@/lib/api";
import { AccessManagement } from "@/components/dashboard/access-management";

export default async function AccessPage() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id || !isRootOwner(session.user.id)) {
    redirect("/dashboard");
  }

  let guilds: { id: string; name: string }[] = [];
  try {
    guilds = (await api.listGuilds()).map((g) => ({ id: String(g.id), name: g.name }));
  } catch {
    /* list may fail; grants still show IDs */
  }

  return <AccessManagement guilds={guilds} />;
}
