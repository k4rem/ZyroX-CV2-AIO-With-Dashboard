import * as React from "react";
import Link from "next/link";
import { Check, ChevronRight, Minus } from "lucide-react";
import type { ModuleMeter, ModuleRow } from "@/lib/loadOverview";
import { DOMAIN_LABELS, DOMAIN_ORDER } from "@/lib/overviewModel";
import { SectionRule } from "@/components/ui/section-rule";
import { SegmentMeter } from "@/components/ui/segment-meter";
import { StatusLabel } from "@/components/ui/status";
import { Tooltip } from "@/components/ui/tooltip";
import { ChangeMark } from "@/components/ui/readout";

function MeterCell({ meter, name }: { meter: ModuleMeter; name: string }) {
  const body = (
    <span className="inline-flex items-center gap-2">
      <SegmentMeter value={meter.value} total={meter.total} tone={meter.tone} label={`${name}: ${meter.label}`} />
      <span className="font-mono text-caption tabular-nums text-fg-3" dir="auto">
        {meter.label}
      </span>
    </span>
  );
  if (!meter.steps) return body;
  return (
    <Tooltip
      side="bottom"
      align="start"
      content={
        <ul className="space-y-0.5">
          {meter.steps.map((s) => (
            <li key={s.label} className="flex items-center gap-1.5">
              {s.done ? (
                <Check className="size-3 text-ok" aria-hidden="true" />
              ) : (
                <Minus className="size-3 text-fg-3" aria-hidden="true" />
              )}
              <span className={s.done ? "text-fg-1" : "text-fg-2"}>{s.label}</span>
              <span className="sr-only">{s.done ? "done" : "not done"}</span>
            </li>
          ))}
        </ul>
      }
    >
      <span tabIndex={0} className="rounded-xs">
        {body}
      </span>
    </Tooltip>
  );
}

function MatrixRow({ row }: { row: ModuleRow }) {
  return (
    <li className="cls-row group grid grid-cols-[minmax(0,1fr)_auto] items-center gap-x-4 gap-y-1 border-b border-line-subtle px-2 py-2.5 hover:bg-surface-2 md:grid-cols-[9rem_7.5rem_minmax(0,1fr)_auto] 2xl:grid-cols-[9.5rem_7.5rem_10.5rem_minmax(0,1fr)_auto]">
      <span className="truncate text-body font-medium text-fg-1">{row.name}</span>
      <span className="justify-self-end md:justify-self-start">
        <ChangeMark watch={row.status}>
          <StatusLabel status={row.status}>{row.statusLabel}</StatusLabel>
        </ChangeMark>
      </span>
      <span className="col-span-2 hidden min-w-0 md:col-span-1 2xl:block">
        {row.meter ? <MeterCell meter={row.meter} name={row.name} /> : null}
      </span>
      <span className="col-span-2 flex min-w-0 flex-wrap items-center gap-x-3 gap-y-1 md:col-span-1">
        <span className="min-w-0 truncate text-small text-fg-2" dir="auto">
          {row.detail}
        </span>
        {row.meter ? (
          <span className="2xl:hidden">
            <MeterCell meter={row.meter} name={row.name} />
          </span>
        ) : null}
      </span>
      <Link
        href={row.href}
        className="col-span-2 -my-3 inline-flex items-center gap-1 justify-self-start rounded-xs py-3 text-small md:-my-1.5 md:py-1.5 text-fg-3 transition-colors duration-micro hover:text-brand-300 focus-visible:text-brand-300 group-hover:text-fg-1 md:col-span-1 md:justify-self-end"
      >
        Configure<span className="sr-only"> {row.name}</span>
        <span className="cls-row-go inline-flex" aria-hidden="true">
          <ChevronRight className="cls-mirror size-3.5" />
        </span>
      </Link>
    </li>
  );
}

/**
 * Module matrix (RP §1.1): every surfaced module grouped by domain, one hairline
 * row each — state, the fact behind it, and a meter only where a real ratio exists.
 */
export function ModuleMatrix({
  modules,
  className,
  style,
}: {
  modules: ModuleRow[];
  className?: string;
  style?: React.CSSProperties;
}) {
  const on = modules.filter((m) => m.bucket === "on").length;
  const groups = DOMAIN_ORDER.map((domain) => ({
    domain,
    rows: modules.filter((m) => m.domain === domain),
  })).filter((g) => g.rows.length > 0);

  return (
    <section aria-labelledby="ov-modules" className={className} style={style}>
      <SectionRule id="ov-modules" label="Modules" meta={`${on} of ${modules.length} on`} />
      <div className="mt-2 4xl:columns-2 4xl:gap-x-10">
        {groups.map((g) => (
          <div key={g.domain} role="group" aria-labelledby={`ov-domain-${g.domain}`} className="mb-3 break-inside-avoid last:mb-0">
            <h3
              id={`ov-domain-${g.domain}`}
              className="flex items-center gap-2 border-b border-line-subtle bg-surface-1/60 px-2 py-1.5 text-small font-medium text-fg-3"
            >
              {DOMAIN_LABELS[g.domain]}
              <span className="font-mono text-caption tabular-nums text-fg-4">{g.rows.length}</span>
            </h3>
            <ul>
              {g.rows.map((row) => (
                <MatrixRow key={row.key} row={row} />
              ))}
            </ul>
          </div>
        ))}
      </div>
    </section>
  );
}
