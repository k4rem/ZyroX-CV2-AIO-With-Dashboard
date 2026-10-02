import * as React from "react";
import { CircleAlert, CircleCheck, Info, Lock, OctagonAlert, TriangleAlert, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";

/**
 * Empty / error / not-configured states (DS §25). Each looks different on purpose
 * so users can tell them apart at a glance. No illustrations, no jokes, no apologies.
 */

export interface StateBlockProps {
  icon?: LucideIcon;
  title: string;
  description?: React.ReactNode;
  actions?: React.ReactNode;
  /** Small monospace line, e.g. the error digest. */
  reference?: string;
  className?: string;
  /** Fill a whole content region (route-level states). */
  fill?: boolean;
}

/** Neutral block: empty, no data yet, no permission, not configured. */
export function EmptyState({ icon: Icon = Info, title, description, actions, reference, className, fill }: StateBlockProps) {
  return (
    <div
      className={cn(
        "flex flex-col items-center justify-center px-4 py-10 text-center",
        fill && "min-h-[50dvh]",
        className,
      )}
    >
      <Icon className="size-6 text-fg-3" strokeWidth={1.5} aria-hidden="true" />
      <h2 className="mt-3 text-section text-fg-1">{title}</h2>
      {description ? <p className="mt-1 max-w-[52ch] text-body-prose text-fg-2" dir="auto">{description}</p> : null}
      {actions ? <div className="mt-4 flex flex-wrap items-center justify-center gap-2">{actions}</div> : null}
      {reference ? <p className="mt-4 font-mono text-caption text-fg-3" dir="ltr">{reference}</p> : null}
    </div>
  );
}

/** Permission state: neutral, never danger-coloured (DS §25). */
export function NoPermissionState(props: Omit<StateBlockProps, "icon">) {
  return <EmptyState icon={Lock} {...props} />;
}

type Tone = "danger" | "warning" | "info" | "neutral" | "ok" | "locked";

const TONES: Record<Tone, { icon: LucideIcon; box: string; glyph: string }> = {
  danger: { icon: OctagonAlert, box: "border-danger/30 bg-danger/[0.08]", glyph: "text-danger" },
  warning: { icon: TriangleAlert, box: "border-warn/30 bg-warn/[0.08]", glyph: "text-warn" },
  info: { icon: Info, box: "border-info/30 bg-info/[0.08]", glyph: "text-info" },
  ok: { icon: CircleCheck, box: "border-ok/30 bg-ok/[0.08]", glyph: "text-ok" },
  locked: { icon: Lock, box: "border-locked/40 bg-locked/[0.08]", glyph: "text-locked" },
  neutral: { icon: CircleAlert, box: "border-line-strong bg-surface-2", glyph: "text-fg-3" },
};

/** Inline banner for a failed or degraded region; the rest of the page keeps working. */
export function InlineBanner({
  tone = "danger",
  title,
  children,
  actions,
  reference,
  className,
}: {
  tone?: Tone;
  title?: string;
  children?: React.ReactNode;
  actions?: React.ReactNode;
  reference?: string;
  className?: string;
}) {
  const t = TONES[tone];
  const Icon = t.icon;
  return (
    <div
      role={tone === "danger" ? "alert" : "status"}
      className={cn("flex items-start gap-3 rounded-md border px-3 py-2.5", t.box, className)}
    >
      <Icon className={cn("mt-0.5 size-4 shrink-0", t.glyph)} strokeWidth={1.75} aria-hidden="true" />
      <div className="min-w-0 flex-1">
        {title ? <p className="text-body font-medium text-fg-1">{title}</p> : null}
        {children ? <div className="text-body text-fg-2">{children}</div> : null}
        {reference ? <p className="mt-1 font-mono text-caption text-fg-3" dir="ltr">{reference}</p> : null}
      </div>
      {actions ? <div className="flex shrink-0 items-center gap-2">{actions}</div> : null}
    </div>
  );
}

/**
 * Failure block (DS §25): a request or render failed. Danger-toned glyph, plain title,
 * one sentence of cause, optional reference (digest), recovery actions.
 */
export function ErrorState({ title, description, actions, reference, className, fill }: Omit<StateBlockProps, "icon">) {
  return (
    <div
      role="alert"
      className={cn(
        "flex flex-col items-center justify-center px-4 py-10 text-center",
        fill && "min-h-[50dvh]",
        className,
      )}
    >
      <OctagonAlert className="size-6 text-danger" strokeWidth={1.5} aria-hidden="true" />
      <h2 className="mt-3 text-section text-fg-1">{title}</h2>
      {description ? <p className="mt-1 max-w-[52ch] text-body-prose text-fg-2" dir="auto">{description}</p> : null}
      {actions ? <div className="mt-4 flex flex-wrap items-center justify-center gap-2">{actions}</div> : null}
      {reference ? <p className="mt-4 font-mono text-caption text-fg-3" dir="ltr">{reference}</p> : null}
    </div>
  );
}
