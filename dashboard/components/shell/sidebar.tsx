"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { PanelLeftClose, PanelLeftOpen, X } from "lucide-react";
import { cn } from "@/lib/utils";
import { DrawerClose } from "@/components/ui/drawer";
import { IconButton } from "@/components/ui/icon-button";
import { buildNav, parseDashboardPath } from "@/lib/shellNav";
import { Wordmark } from "@/components/brand/wordmark";
import { Tooltip } from "@/components/ui/tooltip";
import { GuildSwitcher } from "./guild-switcher";
import { SidebarItem } from "./sidebar-item";
import type { ShellGuild } from "./shell-types";

export const SIDEBAR_ID = "cls-sidebar";

/**
 * Sidebar content, shared by the desktop column and the mobile drawer (DS §14).
 * `collapsed` = 56 px icon rail. Root-only items are present only when the server
 * told the shell `isRoot`; this component never inspects an owner id itself.
 */
export function SidebarContent({
  guilds,
  guildsError,
  isRoot,
  collapsed = false,
  onToggle,
  onNavigate,
  mobile = false,
}: {
  guilds: ShellGuild[];
  guildsError: string | null;
  isRoot: boolean;
  collapsed?: boolean;
  onToggle?: () => void;
  onNavigate?: () => void;
  mobile?: boolean;
}) {
  const pathname = usePathname() ?? "/dashboard";
  const { guildId } = parseDashboardPath(pathname);
  const groups = buildNav({ pathname, guildId, isRoot });
  const rail = collapsed && !mobile;

  return (
    <div className="flex h-full min-h-0 flex-col">
      <div
        className={cn(
          "flex h-topbar shrink-0 items-center border-b border-line",
          rail ? "justify-center px-0" : mobile ? "justify-between ps-3 pe-1.5" : "px-3",
        )}
      >
        <Link
          href="/dashboard/guilds"
          prefetch={false}
          onClick={onNavigate}
          aria-label="CLS OS, all servers"
          className="rounded-sm outline-none focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-4 focus-visible:outline-brand-400"
        >
          <Wordmark showText={!rail} markHeight={rail ? 22 : 20} />
        </Link>
        {mobile ? (
          <DrawerClose asChild>
            <IconButton label="Close navigation" size="icon-lg" tooltipSide="start">
              <X className="size-4" strokeWidth={1.5} aria-hidden="true" />
            </IconButton>
          </DrawerClose>
        ) : null}
      </div>

      <div className={cn("shrink-0 border-b border-line", rail ? "p-2" : "p-2.5")}>
        <GuildSwitcher guilds={guilds} guildsError={guildsError} collapsed={rail} onNavigate={onNavigate} />
      </div>

      <nav aria-label="Primary" className="min-h-0 flex-1 overflow-y-auto overflow-x-hidden px-2 py-3">
        {groups.map((group, i) => {
          // A group holding a single item of the same name (Overview) needs no caption.
          const redundant = group.items.length === 1 && group.items[0].label === group.label;
          return (
            <div key={group.id} role="group" aria-label={group.label} className={cn(i > 0 && "mt-3")}>
              {rail ? (
                i > 0 ? <div role="separator" className="mx-2 mb-2 h-px bg-line" /> : null
              ) : redundant ? null : (
                <p aria-hidden="true" className="cls-overline flex h-5 items-center px-2.5">
                  {group.label}
                </p>
              )}
              <ul className="flex flex-col gap-0.5">
                {group.items.map((item) => (
                  <SidebarItem key={item.id} item={item} collapsed={rail} onNavigate={onNavigate} touch={mobile} />
                ))}
              </ul>
            </div>
          );
        })}
      </nav>

      {mobile || !onToggle ? null : (
        <div className={cn("shrink-0 border-t border-line", rail ? "p-2" : "p-2.5")}>
          <Tooltip content="Expand sidebar" side="end" disabled={!rail} sideOffset={10}>
            <button
              type="button"
              onClick={onToggle}
              aria-expanded={!rail}
              aria-controls={SIDEBAR_ID}
              aria-label={rail ? "Expand sidebar" : "Collapse sidebar"}
              className={cn(
                "flex h-8 w-full items-center gap-2.5 rounded-sm text-body text-fg-3 outline-none transition-colors duration-micro",
                "hover:bg-surface-3 hover:text-fg-1",
                "focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-brand-400",
                rail ? "justify-center px-0" : "px-2.5",
              )}
            >
              {rail ? (
                <PanelLeftOpen className="cls-mirror size-4" strokeWidth={1.5} aria-hidden="true" />
              ) : (
                <>
                  <PanelLeftClose className="cls-mirror size-4" strokeWidth={1.5} aria-hidden="true" />
                  <span>Collapse</span>
                </>
              )}
            </button>
          </Tooltip>
        </div>
      )}
    </div>
  );
}
