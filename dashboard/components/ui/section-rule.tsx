import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Engraved labelled rule (AD §4): the label *is* the section heading, set on a
 * hairline that runs to the inline end. Optional factual `meta` (a count) and an
 * `action` sit on the same line.
 */
export function SectionRule({
  id,
  label,
  meta,
  action,
  as: Heading = "h2",
  className,
}: {
  id?: string;
  label: string;
  meta?: React.ReactNode;
  action?: React.ReactNode;
  as?: "h2" | "h3";
  className?: string;
}) {
  return (
    <div className={cn("flex items-center gap-3", className)}>
      <Heading id={id} className="cls-overline shrink-0 text-fg-2">
        {label}
      </Heading>
      {meta != null && (
        <span className="shrink-0 font-mono text-small tabular-nums text-fg-3" dir="auto">
          {meta}
        </span>
      )}
      <span aria-hidden="true" className="h-px min-w-6 flex-1 bg-line-subtle" />
      {action}
    </div>
  );
}
