import React from "react";
import Image from "next/image";
import Link from "next/link";
import { ChevronRight, Users } from "lucide-react";
import { api, ApiError } from "@/lib/api";
import { getServerSession } from "next-auth/next";
import { authOptions } from "@/lib/auth";
import { redirect } from "next/navigation";
import { PageHeader } from "@/components/dashboard/page-header";
import { ErrorState, EmptyState } from "@/components/ui/state";
import type { GuildSummary } from "@/types/api";

export const dynamic = "force-dynamic";
export const revalidate = 0;

export default async function GuildsPage() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id) {
    redirect("/");
  }

  let guilds: GuildSummary[] = [];
  let error: string | null = null;

  try {
    guilds = await api.listGuilds();
  } catch (err: unknown) {
    if (err instanceof ApiError && err.status === 401) {
      redirect("/?notice=session-ended");
    }
    console.error("Failed to fetch authorized guilds:", err);
    error = err instanceof Error ? err.message : "Failed to load servers.";
  }

  if (!error && guilds.length === 1) {
    redirect(`/dashboard/guild/${guilds[0].id}`);
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="Servers"
        description="Servers your account is authorized to manage through CLS OS."
      />

      {error ? (
        <ErrorState title="Could not load servers" description={error} />
      ) : guilds.length === 0 ? (
        <EmptyState
          title="No authorized servers"
          description="Ask the root owner for a dashboard grant, or verify the bot is in your guild."
          icon={Users}
        />
      ) : (
        <ul className="divide-y divide-line rounded-md border border-line bg-surface-1">
          {guilds.map((guild) => (
            <li key={guild.id}>
              <Link
                href={`/dashboard/guild/${guild.id}`}
                className="flex items-center gap-3 px-3 py-2.5 transition-colors duration-row hover:bg-surface-2"
              >
                {guild.icon_url ? (
                  <Image
                    src={guild.icon_url}
                    alt=""
                    width={36}
                    height={36}
                    className="size-9 shrink-0 rounded-md border border-line object-cover"
                  />
                ) : (
                  <div
                    className="flex size-9 shrink-0 items-center justify-center rounded-md border border-line bg-surface-2 text-caption font-medium text-fg-2"
                    aria-hidden="true"
                  >
                    {guild.name.charAt(0)}
                  </div>
                )}
                <div className="min-w-0 flex-1">
                  <p className="truncate text-body font-medium text-fg-1">{guild.name}</p>
                  <p className="flex items-center gap-2 text-caption text-fg-3">
                    <Users className="size-3.5 shrink-0" aria-hidden="true" />
                    <span className="tabular-nums">{guild.member_count.toLocaleString()} members</span>
                    <span className="text-fg-4" aria-hidden="true">
                      ·
                    </span>
                    <span className="truncate font-mono text-fg-3" dir="ltr">
                      {guild.id}
                    </span>
                  </p>
                </div>
                <ChevronRight className="size-4 shrink-0 text-fg-3 rtl:rotate-180" aria-hidden="true" />
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
