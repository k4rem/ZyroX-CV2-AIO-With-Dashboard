"use client";

import { CircleCheck, CircleOff, Lock, OctagonAlert, TriangleAlert } from "lucide-react";
import { cn } from "@/lib/utils";
import { HEALTH_LABEL, type HealthCheck, type HealthStatus, type ModuleHealth } from "@/lib/platformHealth";
import { TONE_CLASS, toneForHealth } from "@/lib/statusTone";

const GLYPH = {
  healthy: CircleCheck,
  warning: TriangleAlert,
  error: OctagonAlert,
  locked: Lock,
  unavailable: CircleOff,
} as const;

export function HealthBadge({ status, className }: { status: HealthStatus; className?: string }) {
  const tone = TONE_CLASS[toneForHealth(status)];
  const Glyph = GLYPH[status];
  return (
    <span className={cn("inline-flex h-5 items-center gap-1 rounded-xs border px-1.5 text-[11px] font-medium", tone.tint, tone.text, className)}>
      <Glyph className="size-3" strokeWidth={1.75} aria-hidden="true" />
      {HEALTH_LABEL[status]}
    </span>
  );
}

export function InlineHealth({ checks, className }: { checks: HealthCheck[]; className?: string }) {
  const failing = checks.filter((row) => !row.ok);
  if (failing.length === 0) return null;
  const status = failing.some((row) => row.severity === "error") ? "error" : "warning";
  return (
    <p className={cn("mt-1 text-small text-fg-2", className)} role="status">
      <HealthBadge status={status} />
      <span className="ms-2">{failing.map((row) => row.label).join(" · ")}</span>
    </p>
  );
}

export function HealthPanel({ health, className }: { health: ModuleHealth; className?: string }) {
  return (
    <section className={cn("border border-line bg-surface-1", className)}>
      <header className="flex items-center justify-between gap-3 border-b border-line px-3 py-2">
        <h3 className="text-small text-fg-1">Capability</h3>
        <HealthBadge status={health.status} />
      </header>
      <ul className="divide-y divide-line-subtle">
        {health.checks.map((row) => (
          <li key={row.id} className="px-3 py-2">
            <p className="text-small text-fg-1">{row.label}</p>
            {row.ok ? (
              <p className="text-caption text-fg-3">Available</p>
            ) : (
              <p className="text-caption text-fg-2">{row.fix_hint}</p>
            )}
          </li>
        ))}
      </ul>
      <details className="border-t border-line px-3 py-2">
        <summary className="cursor-pointer text-caption text-fg-3">Developer</summary>
        <ul className="mt-2 space-y-1 font-mono text-caption text-fg-4">
          {health.checks.map((row) => (
            <li key={row.id}>{row.id}</li>
          ))}
        </ul>
      </details>
    </section>
  );
}
