"use client";

import * as React from "react";
import * as TooltipPrimitive from "@radix-ui/react-tooltip";
import { useDirection } from "@radix-ui/react-direction";
import { cn } from "@/lib/utils";

/**
 * Tooltip (DS §10.2): 400 ms delay on first hover, none on subsequent hovers
 * within 1 s. Shows on keyboard focus too (Radix). `side` accepts logical
 * `start` / `end` so rail tooltips open away from the sidebar in RTL.
 */
export function TooltipProvider({ children }: { children: React.ReactNode }) {
  return (
    <TooltipPrimitive.Provider delayDuration={400} skipDelayDuration={1000}>
      {children}
    </TooltipPrimitive.Provider>
  );
}

type LogicalSide = "top" | "bottom" | "start" | "end";

export function useResolvedSide(side: LogicalSide): "top" | "bottom" | "left" | "right" {
  const dir = useDirection();
  if (side === "start") return dir === "rtl" ? "right" : "left";
  if (side === "end") return dir === "rtl" ? "left" : "right";
  return side;
}

export interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactElement;
  side?: LogicalSide;
  align?: "start" | "center" | "end";
  sideOffset?: number;
  disabled?: boolean;
  className?: string;
}

export function Tooltip({
  content,
  children,
  side = "bottom",
  align = "center",
  sideOffset = 6,
  disabled,
  className,
}: TooltipProps) {
  const resolved = useResolvedSide(side);
  // The trigger wrapper stays mounted when the tooltip is disabled (e.g. the sidebar rail
  // toggling between rail and expanded) so focus is never lost on the child element.
  const active = !disabled && Boolean(content);
  return (
    <TooltipPrimitive.Root>
      <TooltipPrimitive.Trigger asChild>{children}</TooltipPrimitive.Trigger>
      {active ? (
      <TooltipPrimitive.Portal>
        <TooltipPrimitive.Content
          side={resolved}
          align={align}
          sideOffset={sideOffset}
          collisionPadding={8}
          className={cn(
            "cls-tip z-tooltip max-w-[280px] rounded-sm border border-line-strong bg-surface-2 px-2 py-1 text-small text-fg-1 shadow-elev-1",
            className,
          )}
        >
          {content}
        </TooltipPrimitive.Content>
      </TooltipPrimitive.Portal>
      ) : null}
    </TooltipPrimitive.Root>
  );
}
