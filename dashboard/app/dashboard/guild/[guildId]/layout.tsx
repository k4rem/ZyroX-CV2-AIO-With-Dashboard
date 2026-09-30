/**
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║                                                                  ║
 * ║   ░█▀▀░█▀█░█▀▄░█▀▀░█░█   ░█▀▄░█▀▀░█░█░█▀▀                     ║
 * ║   ░█░░░█░█░█░█░█▀▀░▄▀▄   ░█░█░█▀▀░▀▄▀░▀▀█                     ║
 * ║   ░▀▀▀░▀▀▀░▀▀░░▀▀▀░▀░▀   ░▀▀░░▀▀▀░░▀░░▀▀▀                     ║
 * ║                                                                  ║
 * ║           © 2026 CodeX Devs — All Rights Reserved               ║
 * ║                                                                  ║
 * ║   discord  ──  https://discord.gg/codexdev                      ║
 * ║   youtube  ──  https://youtube.com/@CodeXDevs                   ║
 * ║   github   ──  https://github.com/RayExo                        ║
 * ║                                                                  ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

import React from "react";
import Link from "next/link";
import { redirect } from "next/navigation";
import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ErrorState, NoPermissionState } from "@/components/ui/state";

export const revalidate = 0; // Never cache any guild dashboard page

interface GuildLayoutProps {
  children: React.ReactNode;
  params: { guildId: string };
}

/**
 * Guild gate. The shell already renders identity (breadcrumb, switcher) and navigation,
 * so this layout only authorises the route: the backend must confirm this session may
 * manage the guild before any module page renders. No header card, no tabs.
 */
export default async function GuildLayout({ children, params }: GuildLayoutProps) {
  const { guildId } = params;
  let failure: { status: number; message: string } | null = null;

  try {
    await api.getGuildDetails(guildId);
  } catch (err) {
    if (err instanceof ApiError) {
      if (err.status === 401) redirect("/?notice=session-ended");
      failure = { status: err.status, message: err.message };
    } else {
      failure = { status: 0, message: "The bot API did not respond." };
    }
    console.error("Failed to fetch guild details:", err);
  }

  if (failure) {
    const back = (
      <Button asChild variant="secondary">
        <Link href="/dashboard/guilds" prefetch={false}>
          All servers
        </Link>
      </Button>
    );

    if (failure.status === 403 || failure.status === 404) {
      return (
        <NoPermissionState
          fill
          title="You don't have access to this server"
          description="Your account isn't authorized to manage it, or the bot isn't in it."
          reference={`Server ${guildId}`}
          actions={back}
        />
      );
    }

    return (
      <ErrorState
        fill
        title="Server data could not be loaded"
        description={failure.message}
        reference={failure.status ? `Server ${guildId} · HTTP ${failure.status}` : `Server ${guildId}`}
        actions={back}
      />
    );
  }

  return <>{children}</>;
}
