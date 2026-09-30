"use client";

import Link from "next/link";
import { cn } from "@/lib/utils";
import { Tooltip } from "@/components/ui/tooltip";
import { iconForNav } from "./nav-icons";
import type { ResolvedNavItem } from "@/lib/shellNav";

/**
 * One navigation row (DS §14.2): 32 px, icon 16 px + label. Active = brand tint + fg-1 +
 * a 2 px inline-start bar; that is the only permanent purple in the sidebar.
 * Rail mode hides the label but keeps it as the accessible name and tooltip.
 */
export function SidebarItem({
  item,
  collapsed,
  onNavigate,
  touch = false,
}: {
  item: ResolvedNavItem;
  collapsed: boolean;
  onNavigate?: () => void;
  /** Larger hit area for the mobile drawer. */
  touch?: boolean;
}) {
  const Icon = iconForNav(item.icon);
  return (
    <li>
      <Tooltip content={item.label} side="end" disabled={!collapsed} sideOffset={10}>
        <Link
          href={item.href}
          prefetch={false}
          onClick={onNavigate}
          aria-current={item.active ? "page" : undefined}
          aria-label={collapsed ? item.label : undefined}
          className={cn(
            "group/item relative flex items-center gap-2.5", touch ? "h-10" : "h-8",
            " rounded-sm text-body font-medium outline-none transition-colors duration-micro",
            "focus-visible:outline focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-brand-400",
            collapsed ? "justify-center px-0" : "px-2.5",
            item.active
              ? "bg-brand-600/[0.16] text-fg-1"
              : "text-fg-2 hover:bg-surface-3 hover:text-fg-1",
          )}
        >
          <span
            aria-hidden="true"
            className={cn(
              "pointer-events-none absolute inset-y-2 start-0 w-0.5 rounded-full bg-brand-400 transition-opacity duration-micro",
              item.active ? "opacity-100" : "opacity-0",
            )}
          />
          <Icon
            className={cn("size-4 shrink-0", item.active ? "text-brand-400" : "text-fg-3 group-hover/item:text-fg-2")}
            strokeWidth={1.5}
            aria-hidden="true"
          />
          {collapsed ? null : <span className="truncate">{item.label}</span>}
        </Link>
      </Tooltip>
    </li>
  );
}
