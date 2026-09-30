import * as React from "react";
import { cn } from "@/lib/utils";
import { ClsMark } from "@/components/brand/cls-mark";

/**
 * Wordmark lock-up (DS §12.2): mark + 8 px gap + "CLS OS". "OS" is not coloured
 * differently. `showText={false}` renders the mark alone (icon rail).
 *
 * Set in IBM Plex Sans 600 (the Chakra Petch experiment was dropped; see D7).
 */
export function Wordmark({
  showText = true,
  markHeight = 20,
  className,
}: {
  showText?: boolean;
  markHeight?: number;
  className?: string;
}) {
  return (
    <span className={cn("inline-flex items-center gap-2", className)}>
      <ClsMark height={markHeight} priority />
      {showText ? (
        <span className="cls-wordmark text-fg-1" data-cls-wordmark>
          CLS OS
        </span>
      ) : (
        <span className="sr-only">CLS OS</span>
      )}
    </span>
  );
}
