"use client";

import * as React from "react";

export type SidebarPref = "expanded" | "collapsed";

export const SIDEBAR_COOKIE = "cls_sidebar";

function subscribeMedia(query: string) {
  return (cb: () => void) => {
    const mql = window.matchMedia(query);
    mql.addEventListener("change", cb);
    return () => mql.removeEventListener("change", cb);
  };
}

function useMedia(query: string, serverValue: boolean) {
  const subscribe = React.useMemo(() => subscribeMedia(query), [query]);
  return React.useSyncExternalStore(
    subscribe,
    () => window.matchMedia(query).matches,
    () => serverValue,
  );
}

/**
 * Sidebar model (DS §14):
 *  - ≥ 1280 px: persisted preference (cookie, so the server renders the right width on first paint).
 *  - 1024–1279 px: rail by default; expanding is a transient overlay that never pushes content.
 *  - < 1024 px: off-canvas drawer.
 */
export function useSidebarState(initial: SidebarPref) {
  const isLg = useMedia("(min-width: 1024px)", true);
  const isXl = useMedia("(min-width: 1280px)", true);

  const [pref, setPref] = React.useState<SidebarPref>(initial);
  const [transientOpen, setTransientOpen] = React.useState(false);
  const [drawerOpen, setDrawerOpen] = React.useState(false);

  // The width must not animate on first paint / hydration.
  const [booting, setBooting] = React.useState(true);
  React.useEffect(() => {
    const id = requestAnimationFrame(() => setBooting(false));
    return () => cancelAnimationFrame(id);
  }, []);

  // Leaving a breakpoint resets the transient states.
  React.useEffect(() => {
    if (isXl) setTransientOpen(false);
    if (isLg) setDrawerOpen(false);
  }, [isXl, isLg]);

  const overlay = isLg && !isXl && transientOpen;
  const collapsed = isLg && (isXl ? pref === "collapsed" : !transientOpen);

  const toggle = React.useCallback(() => {
    if (isXl) {
      setPref((p) => {
        const next: SidebarPref = p === "collapsed" ? "expanded" : "collapsed";
        document.cookie = `${SIDEBAR_COOKIE}=${next}; path=/; max-age=31536000; samesite=lax`;
        return next;
      });
    } else {
      setTransientOpen((o) => !o);
    }
  }, [isXl]);

  const closeTransient = React.useCallback(() => setTransientOpen(false), []);

  return { isLg, isXl, collapsed, overlay, toggle, closeTransient, drawerOpen, setDrawerOpen, booting };
}
