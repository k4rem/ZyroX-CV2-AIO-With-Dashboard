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
import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { ApiError, api } from "@/lib/api";
import { isRootOwner } from "@/lib/utils";
import { AppShell } from "@/components/shell/app-shell";
import type { ShellGuild } from "@/components/shell/shell-types";

// Shell-level title only; the landing page metadata belongs to Task B.
export const metadata = { title: "CLS OS" };

// Session + authorized guild list are per-request; never cache the shell.
export const dynamic = "force-dynamic";

/**
 * Dashboard shell (server). Everything authorization-related is decided here, on the
 * server, and handed to the client shell as plain props:
 *  - the session (JWT cookie) must exist, otherwise the user is sent back to sign in;
 *  - `isRoot` is computed from server-only env (never shipped to the browser);
 *  - the guild list is whatever the backend authorises for this session, not Discord
 *    Administrator permission.
 */
export default async function DashboardLayout({ children }: { children: React.ReactNode }) {
  const session = await getServerSession(authOptions);
  const userId = session?.user?.id;
  if (!session || !userId) {
    redirect("/?notice=session-ended");
  }

  const isRoot = isRootOwner(userId);

  let guilds: ShellGuild[] = [];
  let guildsError: string | null = null;
  try {
    const list = await api.listGuilds();
    guilds = list.map((g) => ({
      id: String(g.id),
      name: g.name,
      iconUrl: g.icon_url ?? null,
    }));
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      // Session row revoked/expired server-side: the cookie alone is not enough.
      redirect("/?notice=session-ended");
    }
    guildsError = err instanceof ApiError ? `(${err.status})` : "The bot API did not respond.";
  }

  const jar = cookies();
  const isDev = process.env.NODE_ENV !== "production";
  const dir = isDev && jar.get("cls_dir")?.value === "rtl" ? "rtl" : "ltr";
  const initialSidebar = jar.get("cls_sidebar")?.value === "collapsed" ? "collapsed" : "expanded";

  return (
    <AppShell
      user={{
        id: userId,
        name: session.user?.name ?? null,
        image: session.user?.image ?? null,
      }}
      isRoot={isRoot}
      guilds={guilds}
      guildsError={guildsError}
      dir={dir}
      initialSidebar={initialSidebar}
      showDevTools={isDev}
    >
      {children}
    </AppShell>
  );
}
