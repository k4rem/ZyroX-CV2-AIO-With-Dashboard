"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { ChevronRight } from "lucide-react";
import { cn } from "@/lib/utils";
import { parseDashboardPath, resolveBreadcrumbs } from "@/lib/shellNav";
import type { ShellGuild } from "./shell-types";

/**
 * Breadcrumb trail (DS §15.1). Path segments only; it never duplicates sidebar
 * navigation. Below `md` it collapses to parent + current. Guild names are user
 * content, so they render with dir="auto".
 */
export function Breadcrumbs({ guilds }: { guilds: ShellGuild[] }) {
  const pathname = usePathname() ?? "/dashboard";
  const { guildId } = parseDashboardPath(pathname);
  const guildName = guildId ? guilds.find((g) => g.id === guildId)?.name : undefined;
  const crumbs = resolveBreadcrumbs({ pathname, guildId, guildName });

  const parent = crumbs.length > 1 ? crumbs[crumbs.length - 2] : null;
  const current = crumbs[crumbs.length - 1];

  return (
    <nav aria-label="Breadcrumb" className="min-w-0">
      {/* Below md: two compact lines (where you are in / what you are on) so the guild context is not lost. */}
      {current ? (
        <div aria-hidden="true" className="flex min-w-0 flex-col justify-center leading-tight md:hidden">
          {parent ? (
            <span dir="auto" className="truncate text-small text-fg-3">
              {crumbs.slice(0, -1).map((c) => c.label).join(" / ")}
            </span>
          ) : null}
          <span dir={current.userContent ? "auto" : undefined} className="truncate font-medium text-fg-1">
            {current.label}
          </span>
        </div>
      ) : null}
      <ol className="hidden min-w-0 items-center text-body md:flex">
        {crumbs.map((crumb, i) => {
          const last = i === crumbs.length - 1;
          return (
            <li key={`${i}-${crumb.label}`} className="flex min-w-0 items-center">
              {i > 0 ? (
                <ChevronRight
                  className="cls-mirror mx-1 size-3.5 shrink-0 text-fg-4"
                  strokeWidth={1.5}
                  aria-hidden="true"
                />
              ) : null}
              {crumb.href && !last ? (
                <Link
                  href={crumb.href}
                  prefetch={false}
                  dir={crumb.userContent ? "auto" : undefined}
                  className="max-w-[220px] truncate rounded-xs text-fg-3 outline-none transition-colors duration-micro hover:text-fg-1 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-400"
                >
                  {crumb.label}
                </Link>
              ) : (
                <span
                  dir={crumb.userContent ? "auto" : undefined}
                  aria-current={last ? "page" : undefined}
                  className={cn("max-w-[260px] truncate", last ? "font-medium text-fg-1" : "text-fg-3")}
                >
                  {crumb.label}
                </span>
              )}
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
