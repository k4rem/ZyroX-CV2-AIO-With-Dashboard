import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Panel / surface (DS §9.1): surface-1, 1 px line, inner highlight, no shadow, no glow.
 * Depth comes from the surface ladder, not from shadows.
 */
export const Panel = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement> & { raised?: boolean }>(
  ({ className, raised, ...props }, ref) => (
    <div ref={ref} className={cn(raised ? "cls-raised" : "cls-panel", className)} {...props} />
  ),
);
Panel.displayName = "Panel";

/** 40 px header strip on surface-2 with an overline title. */
export function PanelHeader({
  title,
  actions,
  className,
  children,
}: {
  title?: React.ReactNode;
  actions?: React.ReactNode;
  className?: string;
  children?: React.ReactNode;
}) {
  return (
    <div
      className={cn(
        "flex h-10 items-center gap-2 rounded-t-md border-b border-line-subtle bg-surface-2 px-3",
        className,
      )}
    >
      {title ? <h2 className="cls-overline min-w-0 flex-1 truncate">{title}</h2> : <div className="flex-1">{children}</div>}
      {actions ? <div className="flex items-center gap-1">{actions}</div> : null}
    </div>
  );
}

export function PanelBody({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn("p-4", className)} {...props} />;
}
