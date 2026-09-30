"use client";

import * as React from "react";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";
import { isFluidRoute } from "@/lib/shellNav";
import { Drawer, DrawerContent } from "@/components/ui/drawer";
import { UiProviders } from "@/components/providers/ui-providers";
import { SidebarContent, SIDEBAR_ID } from "./sidebar";
import { Topbar } from "./topbar";
import { useSidebarState, type SidebarPref } from "./use-sidebar-state";
import type { ShellGuild, ShellUser } from "./shell-types";

export interface AppShellProps {
  user: ShellUser;
  /** Server-computed. The browser never sees the owner id it was derived from. */
  isRoot: boolean;
  guilds: ShellGuild[];
  guildsError: string | null;
  dir: "ltr" | "rtl";
  initialSidebar: SidebarPref;
  showDevTools: boolean;
  children: React.ReactNode;
}

/**
 * Dashboard app shell (DS §13): an inverted-L of sidebar + topbar around a single
 * scrolling content column. Sidebar width is the only layout property that animates.
 *
 *   ≥ 1280  sidebar 248 px (or 56 px rail, persisted)
 *   1024–1279  rail 56 px; expanding overlays content
 *   < 1024  off-canvas drawer opened from the topbar
 */
export function AppShell({ user, isRoot, guilds, guildsError, dir, initialSidebar, showDevTools, children }: AppShellProps) {
  const pathname = usePathname();
  const { isLg, collapsed, overlay, toggle, closeTransient, drawerOpen, setDrawerOpen, booting } =
    useSidebarState(initialSidebar);
  const mainRef = React.useRef<HTMLElement>(null);
  const menuRef = React.useRef<HTMLButtonElement>(null);
  const firstPath = React.useRef(pathname);
  // Set when the drawer is closed by choosing a destination: focus then belongs to <main>.
  const closedByNavigation = React.useRef(false);

  // Keep <html dir> in step with the server-selected direction.
  React.useEffect(() => {
    const root = document.documentElement;
    const previous = root.getAttribute("dir");
    root.setAttribute("dir", dir);
    return () => {
      if (previous) root.setAttribute("dir", previous);
    };
  }, [dir]);

  // After a client-side navigation, move focus to the content region so keyboard and
  // screen-reader users land on the new page instead of a stale nav link.
  React.useEffect(() => {
    if (firstPath.current === pathname) return;
    firstPath.current = pathname;
    setDrawerOpen(false);
    closeTransient();
    mainRef.current?.focus({ preventScroll: true });
    window.scrollTo({ top: 0 });
  }, [pathname, setDrawerOpen, closeTransient]);

  // Esc closes the transient rail overlay.
  React.useEffect(() => {
    if (!overlay) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") closeTransient();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [overlay, closeTransient]);

  // `collapsed` already accounts for the overlay case (the overlay keeps the 56 px column).
  const railed = collapsed;
  const column = isLg ? (railed || overlay ? "var(--cls-rail-w)" : "var(--cls-sidebar-w)") : "0px";

  return (
    <UiProviders dir={dir}>
      <div
        className="cls-shell min-h-dvh bg-canvas text-fg-1"
        data-booting={booting ? "true" : "false"}
        style={{ "--cls-shell-col": column } as React.CSSProperties}
      >
        <a
          href="#main"
          className="sr-only focus:not-sr-only focus:fixed focus:start-3 focus:top-3 focus:z-toast focus:rounded-sm focus:border focus:border-line-strong focus:bg-surface-2 focus:px-3 focus:py-1.5 focus:text-body focus:text-fg-1"
        >
          Skip to content
        </a>

        {/* Sidebar column (≥ lg). The aside may exceed the column width: that is the overlay state. */}
        <div className="relative hidden lg:block">
          {overlay ? (
            <button
              type="button"
              tabIndex={-1}
              aria-hidden="true"
              onClick={closeTransient}
              className="fixed inset-0 z-sidebar cursor-default bg-transparent"
            />
          ) : null}
          <aside
            id={SIDEBAR_ID}
            data-state={railed ? "rail" : "expanded"}
            className={cn(
              "sticky top-0 z-sidebar h-dvh overflow-hidden border-e border-line bg-chrome transition-[width] duration-emphasized ease-cls-in-out",
              overlay ? "w-[var(--cls-sidebar-w)] shadow-elev-2" : "w-full",
            )}
          >
            <SidebarContent
              guilds={guilds}
              guildsError={guildsError}
              isRoot={isRoot}
              collapsed={railed && !overlay}
              onToggle={toggle}
              onNavigate={overlay ? closeTransient : undefined}
            />
          </aside>
        </div>

        <div className="flex min-h-dvh min-w-0 flex-col">
          <Topbar
            user={user}
            isRoot={isRoot}
            guilds={guilds}
            dir={dir}
            showDevTools={showDevTools}
            drawerOpen={drawerOpen}
            onOpenDrawer={() => setDrawerOpen(true)}
            menuRef={menuRef}
          />
          <main
            id="main"
            ref={mainRef}
            tabIndex={-1}
            className="min-w-0 flex-1 outline-none"
          >
            <div
              key={pathname}
              className={cn(
                "cls-route-fade mx-auto w-full px-4 py-5 md:px-6 md:py-6 3xl:px-8",
                isFluidRoute(pathname) ? "max-w-none" : "max-w-content",
              )}
            >
              {children}
            </div>
          </main>
        </div>

        {/* Mobile drawer (< lg) */}
        {isLg ? null : (
          <Drawer open={drawerOpen} onOpenChange={setDrawerOpen}>
            <DrawerContent
              title="Navigation"
              onCloseAutoFocus={(e) => {
                e.preventDefault();
                if (closedByNavigation.current) {
                  closedByNavigation.current = false;
                  return;
                }
                menuRef.current?.focus();
              }}
            >
              <SidebarContent
                guilds={guilds}
                guildsError={guildsError}
                isRoot={isRoot}
                mobile
                onNavigate={() => {
                  closedByNavigation.current = true;
                  setDrawerOpen(false);
                }}
              />
            </DrawerContent>
          </Drawer>
        )}
      </div>
    </UiProviders>
  );
}
