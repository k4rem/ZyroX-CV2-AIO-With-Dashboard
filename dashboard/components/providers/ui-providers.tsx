"use client";

import * as React from "react";
import * as Direction from "@radix-ui/react-direction";
import { TooltipProvider } from "@/components/ui/tooltip";

/**
 * Radix direction + tooltip context for the dashboard subtree. Direction is chosen
 * by the server layout, so portalled overlays (popover, menu, tooltip) align
 * correctly in RTL as well.
 */
export function UiProviders({ dir, children }: { dir: "ltr" | "rtl"; children: React.ReactNode }) {
  return (
    <Direction.Provider dir={dir}>
      <TooltipProvider>{children}</TooltipProvider>
    </Direction.Provider>
  );
}
