import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { api, ApiError } from "@/lib/api";
import { resolvePostAuthDestination } from "@/lib/authRouting";
import { isRootOwner } from "@/lib/utils";
import { AuthContinueClient } from "@/components/auth/auth-continue-client";

export const dynamic = "force-dynamic";

export default async function AuthContinuePage({
  searchParams,
}: {
  searchParams: { callbackUrl?: string };
}) {
  const session = await getServerSession(authOptions);
  const userId = session?.user?.id;
  if (!session || !userId) {
    redirect("/?notice=session-ended");
  }

  let guildIds: string[] = [];
  try {
    const list = await api.listGuilds();
    guildIds = list.map((g) => String(g.id));
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      redirect("/?notice=session-ended");
    }
    redirect("/auth/error?error=ServiceUnavailable");
  }

  const destination = resolvePostAuthDestination({
    guildIds,
    isRoot: isRootOwner(userId),
    callbackUrl: searchParams.callbackUrl,
  });

  if (destination === "/auth/no-access") {
    redirect("/auth/no-access");
  }

  return (
    <AuthContinueClient
      destination={destination}
      userName={session.user?.name ?? null}
      userImage={session.user?.image ?? null}
    />
  );
}
