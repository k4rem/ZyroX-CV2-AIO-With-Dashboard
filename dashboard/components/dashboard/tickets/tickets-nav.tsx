"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const LINKS = [
  { href: "", label: "Queue" },
  { href: "/panels", label: "Panels" },
  { href: "/categories", label: "Categories & Teams" },
  { href: "/settings", label: "Settings" },
  { href: "/transcripts", label: "Transcripts" },
];

export function TicketsNav({ guildId }: { guildId: string }) {
  const pathname = usePathname();
  const base = `/dashboard/guild/${guildId}/tickets`;
  return (
    <nav className="mb-4 flex min-w-0 max-w-full gap-1 overflow-x-auto border-b border-line-subtle" aria-label="Tickets">
      {LINKS.map((link) => {
        const href = `${base}${link.href}`;
        const active = link.href === "" ? pathname === base : pathname === href || pathname.startsWith(`${href}/`);
        return (
          <Link
            key={link.href}
            href={href}
            className={cn(
              "shrink-0 border-b-2 px-3 py-2 text-small",
              active ? "border-accent text-fg-1" : "border-transparent text-fg-3 hover:text-fg-1",
            )}
            aria-current={active ? "page" : undefined}
          >
            {link.label}
          </Link>
        );
      })}
    </nav>
  );
}
