"use client";

import type * as React from "react";
import { Menu } from "lucide-react";
import { IconButton } from "@/components/ui/icon-button";
import { Breadcrumbs } from "./breadcrumbs";
import { HealthIndicator } from "./health-indicator";
import { UserMenu } from "./user-menu";
import type { ShellGuild, ShellUser } from "./shell-types";

/**
 * Global topbar (DS §15): 48 px, inverted-L partner of the sidebar. Left = drawer
 * trigger (< lg) + breadcrumbs. Right = bot health + account. No navigation is
 * duplicated here.
 */
export function Topbar({
  user,
  isRoot,
  guilds,
  dir,
  showDevTools,
  drawerOpen,
  onOpenDrawer,
  menuRef,
}: {
  user: ShellUser;
  isRoot: boolean;
  guilds: ShellGuild[];
  dir: "ltr" | "rtl";
  showDevTools: boolean;
  drawerOpen: boolean;
  onOpenDrawer: () => void;
  /** Receives focus when the drawer closes without navigating. */
  menuRef?: React.Ref<HTMLButtonElement>;
}) {
  return (
    <header className="sticky top-0 z-topbar flex h-topbar shrink-0 items-center gap-2 border-b border-line bg-chrome px-3 md:px-6 3xl:px-8">
      <IconButton
        ref={menuRef}
        label="Open navigation"
        size="icon-lg"
        onClick={onOpenDrawer}
        aria-expanded={drawerOpen}
        aria-haspopup="dialog"
        className="-ms-1 lg:hidden"
        tooltipSide="end"
      >
        <Menu className="size-4" strokeWidth={1.5} aria-hidden="true" />
      </IconButton>

      <div className="min-w-0 flex-1">
        <Breadcrumbs guilds={guilds} />
      </div>

      <div className="flex shrink-0 items-center gap-1">
        <HealthIndicator />
        <span aria-hidden="true" className="mx-1 h-4 w-px bg-line" />
        <UserMenu user={user} isRoot={isRoot} dir={dir} showDevTools={showDevTools} />
      </div>
    </header>
  );
}
