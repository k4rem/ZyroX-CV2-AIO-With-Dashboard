"use client";

import * as React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { Check, ChevronsUpDown, Search, Server } from "lucide-react";
import { cn } from "@/lib/utils";
import { Popover, PopoverClose, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Tooltip, useResolvedSide } from "@/components/ui/tooltip";
import { Avatar } from "@/components/ui/avatar";
import { parseDashboardPath, switchGuildHref } from "@/lib/shellNav";
import type { ShellGuild } from "./shell-types";

const SEARCH_THRESHOLD = 6;

/**
 * Guild identity + switcher (DS §15.2). The list is exactly the set of guilds the
 * backend authorised for this session; nothing here derives authorisation.
 */
export function GuildSwitcher({
  guilds,
  guildsError,
  collapsed,
  onNavigate,
}: {
  guilds: ShellGuild[];
  guildsError: string | null;
  collapsed: boolean;
  onNavigate?: () => void;
}) {
  const pathname = usePathname() ?? "/dashboard";
  const { guildId } = parseDashboardPath(pathname);
  const current = guildId ? guilds.find((g) => g.id === guildId) : undefined;
  const [query, setQuery] = React.useState("");
  const [open, setOpen] = React.useState(false);
  const popSide = useResolvedSide(collapsed ? "end" : "bottom");

  const filtered = React.useMemo(() => {
    const q = query.trim().toLowerCase();
    return q ? guilds.filter((g) => g.name.toLowerCase().includes(q)) : guilds;
  }, [guilds, query]);

  const label = current?.name ?? (guildId ? `Server ${guildId}` : "Select server");

  const trigger = (
    <button
      type="button"
      aria-label={collapsed ? `Server: ${label}. Switch server` : undefined}
      className={cn(
        "flex h-10 w-full items-center gap-2 rounded-sm border border-line bg-surface-1 text-start outline-none transition-colors duration-micro",
        "hover:border-line-strong hover:bg-surface-2",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand-400",
        "data-[state=open]:border-line-strong data-[state=open]:bg-surface-2",
        collapsed ? "justify-center px-0" : "px-2",
      )}
    >
      {current || guildId ? (
        <Avatar src={current?.iconUrl} name={current?.name ?? label} size={24} />
      ) : (
        <span className="inline-flex size-6 shrink-0 items-center justify-center rounded-full bg-surface-3 text-fg-3">
          <Server className="size-3.5" strokeWidth={1.5} aria-hidden="true" />
        </span>
      )}
      {collapsed ? null : (
        <>
          <span className="min-w-0 flex-1">
            <span className="block truncate text-body font-medium leading-4 text-fg-1" dir="auto">
              {label}
            </span>
            <span className="block truncate text-small leading-4 text-fg-3">
              {guildId ? "Switch server" : "No server selected"}
            </span>
          </span>
          <ChevronsUpDown className="size-4 shrink-0 text-fg-3" strokeWidth={1.5} aria-hidden="true" />
        </>
      )}
    </button>
  );

  return (
    <Popover
      open={open}
      onOpenChange={(o) => {
        setOpen(o);
        if (!o) setQuery("");
      }}
    >
      <Tooltip content={label} side="end" sideOffset={10} disabled={!collapsed || open}>
        <PopoverTrigger asChild>{trigger}</PopoverTrigger>
      </Tooltip>
      <PopoverContent align="start" side={popSide} className="w-[260px]">
        {guilds.length > SEARCH_THRESHOLD ? (
          <div className="relative border-b border-line p-2">
            <Search
              className="pointer-events-none absolute start-4 top-1/2 size-3.5 -translate-y-1/2 text-fg-3"
              strokeWidth={1.5}
              aria-hidden="true"
            />
            <input
              type="search"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Find a server"
              aria-label="Find a server"
              autoFocus
              className="h-7 w-full rounded-sm border border-line-input bg-surface-well ps-8 pe-2 text-body text-fg-1 placeholder:text-fg-3 focus-visible:border-brand-400 focus-visible:outline-brand-400 focus-visible:outline-offset-0"
            />
          </div>
        ) : null}

        <div className="max-h-[320px] overflow-y-auto p-1">
          {guildsError ? (
            <p className="px-2 py-3 text-small text-fg-3">Servers could not be loaded. {guildsError}</p>
          ) : filtered.length === 0 ? (
            <p className="px-2 py-3 text-small text-fg-3">
              {guilds.length === 0 ? "No servers are linked to your account." : "No server matches that search."}
            </p>
          ) : (
            <ul>
              {filtered.map((g) => {
                const selected = g.id === guildId;
                return (
                  <li key={g.id}>
                    <PopoverClose asChild>
                      <Link
                        href={switchGuildHref(pathname, g.id)}
                        prefetch={false}
                        onClick={onNavigate}
                        aria-current={selected ? "true" : undefined}
                        className={cn(
                          "flex h-9 items-center gap-2 rounded-sm px-2 text-body outline-none transition-colors duration-micro",
                          "hover:bg-surface-3 focus-visible:bg-surface-3 focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-brand-400",
                          selected ? "text-fg-1" : "text-fg-2 hover:text-fg-1",
                        )}
                      >
                        <Avatar src={g.iconUrl} name={g.name} size={20} />
                        <span className="min-w-0 flex-1 truncate" dir="auto">
                          {g.name}
                        </span>
                        {selected ? <Check className="size-4 shrink-0 text-fg-2" strokeWidth={1.5} aria-hidden="true" /> : null}
                      </Link>
                    </PopoverClose>
                  </li>
                );
              })}
            </ul>
          )}
        </div>

        <div className="border-t border-line p-1">
          <PopoverClose asChild>
            <Link
              href="/dashboard/guilds"
              prefetch={false}
              onClick={onNavigate}
              className="flex h-8 items-center gap-2 rounded-sm px-2 text-body text-fg-2 outline-none transition-colors duration-micro hover:bg-surface-3 hover:text-fg-1 focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-brand-400"
            >
              <Server className="size-4 shrink-0" strokeWidth={1.5} aria-hidden="true" />
              All servers
            </Link>
          </PopoverClose>
        </div>
      </PopoverContent>
    </Popover>
  );
}
