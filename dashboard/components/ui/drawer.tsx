"use client";

import * as React from "react";
import * as DialogPrimitive from "@radix-ui/react-dialog";
import { cn } from "@/lib/utils";

/**
 * Drawer (DS §22, §15.6): a dialog docked to the inline-start or inline-end edge.
 * Uses logical `start-0` / `end-0`, so it follows `dir`. The slide offset flips
 * through --cls-dir; reduced motion swaps the slide for a 120 ms fade.
 */
const Drawer = DialogPrimitive.Root;
const DrawerTrigger = DialogPrimitive.Trigger;
const DrawerClose = DialogPrimitive.Close;

export interface DrawerContentProps extends React.ComponentPropsWithoutRef<typeof DialogPrimitive.Content> {
  side?: "start" | "end";
  /** Accessible name (required by the dialog role). */
  title: string;
  width?: string;
}

const DrawerContent = React.forwardRef<React.ElementRef<typeof DialogPrimitive.Content>, DrawerContentProps>(
  ({ className, children, side = "start", title, width = "min(320px, 85vw)", style, ...props }, ref) => (
    <DialogPrimitive.Portal>
      <DialogPrimitive.Overlay
        className="cls-scrim fixed inset-0 z-scrim bg-[rgb(var(--cls-scrim)/0.72)]"
      />
      <DialogPrimitive.Content
        ref={ref}
        aria-describedby={undefined}
        style={{ width, ...style }}
        className={cn(
          "cls-drawer fixed inset-y-0 z-drawer flex flex-col bg-chrome outline-none",
          side === "start"
            ? "start-0 border-e border-line-strong"
            : "cls-drawer-end end-0 border-s border-line-strong",
          className,
        )}
        {...props}
      >
        <DialogPrimitive.Title className="sr-only">{title}</DialogPrimitive.Title>
        {children}
      </DialogPrimitive.Content>
    </DialogPrimitive.Portal>
  ),
);
DrawerContent.displayName = "DrawerContent";

export { Drawer, DrawerTrigger, DrawerClose, DrawerContent };
