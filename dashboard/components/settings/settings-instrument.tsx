import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * A short settings page keeps a deliberate measure instead of stretching
 * across the shell and leaving an empty canvas.
 */
export function SettingsInstrument({
  children,
  summary,
  wide = false,
  className,
}: {
  children: React.ReactNode;
  summary?: React.ReactNode;
  wide?: boolean;
  className?: string;
}) {
  return (
    <div className={cn(wide ? "max-w-[52rem]" : "max-w-[36rem]", className)}>
      {summary ? (
        <p className="mb-4 text-small text-fg-2" dir="auto">
          {summary}
        </p>
      ) : null}
      {children}
    </div>
  );
}
