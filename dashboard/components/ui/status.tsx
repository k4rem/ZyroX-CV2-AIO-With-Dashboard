import * as React from "react";
import {
  CircleAlert,
  CircleCheck,
  CircleDashed,
  CircleHelp,
  CircleMinus,
  CircleOff,
  OctagonAlert,
  TriangleAlert,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Status system (DS §23): colour + shape + text, never colour alone.
 * Statuses are never purple. "Legacy", "Root" etc. are not statuses.
 */
export type Status =
  | "healthy"
  | "online"
  | "offline"
  | "warning"
  | "degraded"
  | "critical"
  | "pending"
  | "disabled"
  | "unknown";

type Shape = "solid" | "ring" | "dashed" | "half";

const STATUS: Record<
  Status,
  { label: string; shape: Shape; text: string; bg: string; border: string; tint: string; glyph: LucideIcon }
> = {
  healthy: { label: "Healthy", shape: "solid", text: "text-ok", bg: "bg-ok", border: "border-ok", tint: "bg-ok/[0.12] border-ok/[0.32]", glyph: CircleCheck },
  online: { label: "Online", shape: "solid", text: "text-ok", bg: "bg-ok", border: "border-ok", tint: "bg-ok/[0.12] border-ok/[0.32]", glyph: CircleCheck },
  offline: { label: "Offline", shape: "ring", text: "text-neutral", bg: "bg-neutral", border: "border-neutral", tint: "bg-neutral/[0.12] border-neutral/[0.32]", glyph: CircleOff },
  warning: { label: "Warning", shape: "solid", text: "text-warn", bg: "bg-warn", border: "border-warn", tint: "bg-warn/[0.12] border-warn/[0.32]", glyph: TriangleAlert },
  degraded: { label: "Degraded", shape: "half", text: "text-warn", bg: "bg-warn", border: "border-warn", tint: "bg-warn/[0.12] border-warn/[0.32]", glyph: CircleAlert },
  critical: { label: "Critical", shape: "solid", text: "text-danger", bg: "bg-danger", border: "border-danger", tint: "bg-danger/[0.12] border-danger/[0.32]", glyph: OctagonAlert },
  pending: { label: "Pending", shape: "dashed", text: "text-info", bg: "bg-info", border: "border-info", tint: "bg-info/[0.12] border-info/[0.32]", glyph: CircleDashed },
  disabled: { label: "Disabled", shape: "ring", text: "text-fg-3", bg: "bg-fg-4", border: "border-fg-4", tint: "bg-fg-4/[0.12] border-fg-4/[0.32]", glyph: CircleMinus },
  unknown: { label: "Unknown", shape: "dashed", text: "text-neutral", bg: "bg-neutral", border: "border-neutral", tint: "bg-neutral/[0.12] border-neutral/[0.32]", glyph: CircleHelp },
};

export function statusLabelText(status: Status) {
  return STATUS[status].label;
}

/** 6 px shape. `live` adds the one sanctioned pulse ring (global bot indicator / live feeds). */
export function StatusDot({
  status,
  live = false,
  className,
}: {
  status: Status;
  live?: boolean;
  className?: string;
}) {
  const s = STATUS[status];
  return (
    <span aria-hidden="true" className={cn("relative inline-flex size-1.5 shrink-0", className)}>
      {live ? <span className={cn("cls-pulse-ring absolute inset-0 rounded-full", s.bg)} /> : null}
      <span
        className={cn(
          "relative inline-block size-1.5 rounded-full",
          s.shape === "solid" && s.bg,
          s.shape === "ring" && cn("border", s.border),
          s.shape === "dashed" && cn("border border-dashed", s.border),
          s.shape === "half" && cn("border", s.border),
        )}
        style={
          s.shape === "half"
            ? { backgroundImage: "linear-gradient(to bottom, currentColor 50%, transparent 50%)" }
            : undefined
        }
      />
    </span>
  );
}

/** Default rendering: dot + text, no background (DS §23 form 1). */
export function StatusLabel({
  status,
  live,
  children,
  className,
}: {
  status: Status;
  live?: boolean;
  children?: React.ReactNode;
  className?: string;
}) {
  const s = STATUS[status];
  return (
    <span className={cn("inline-flex items-center gap-1.5 text-small text-fg-2", s.text, className)}>
      <StatusDot status={status} live={live} />
      <span className="text-fg-2">{children ?? s.label}</span>
    </span>
  );
}

/** Table/incident chip (DS §23 form 2): 20 px, radius-xs, tinted. Never purple. */
export function StatusChip({
  status,
  children,
  className,
}: {
  status: Status;
  children?: React.ReactNode;
  className?: string;
}) {
  const s = STATUS[status];
  const Glyph = s.glyph;
  return (
    <span
      className={cn(
        "inline-flex h-5 items-center gap-1 rounded-xs border px-1.5 text-[11px] font-medium",
        s.tint,
        s.text,
        className,
      )}
    >
      <Glyph className="size-3" strokeWidth={1.75} aria-hidden="true" />
      {children ?? s.label}
    </span>
  );
}
