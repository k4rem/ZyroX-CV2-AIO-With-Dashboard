import * as React from "react";
import type { OverviewPayload } from "@/lib/loadOverview";
import { COVERAGE_LABELS, COVERAGE_ORDER, type CoverageBucket } from "@/lib/overviewModel";
import { SectionRule } from "@/components/ui/section-rule";
import { StateBar } from "@/components/ui/state-bar";
import { MicroBars } from "@/components/ui/micro-bar";
import { cn } from "@/lib/utils";

const COVERAGE_FILL: Record<CoverageBucket, string> = {
  on: "bg-ok",
  partial: "bg-warn",
  off: "bg-fg-4",
  unavailable: "bg-neutral",
};

function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-line-subtle py-1.5 last:border-b-0">
      <dt className="text-small text-fg-2">{label}</dt>
      <dd className="min-w-0 truncate text-end font-mono text-body tabular-nums text-fg-1">{children}</dd>
    </div>
  );
}

/** Facts column (RP §1.1): composition and plain facts — no statuses to act on here. */
export function FactsColumn({
  data,
  className,
  style,
}: {
  data: OverviewPayload;
  className?: string;
  style?: React.CSSProperties;
}) {
  const g = data.guild;
  const parts = COVERAGE_ORDER.filter((b) => b !== "unavailable" || data.coverage.unavailable > 0).map((b) => ({
    key: b,
    label: COVERAGE_LABELS[b],
    value: data.coverage[b],
    fill: COVERAGE_FILL[b],
  }));

  return (
    <div className={cn("grid content-start gap-x-8 gap-y-7 md:grid-cols-3 xl:grid-cols-1", className)} style={style}>
      <section aria-labelledby="ov-state">
        <SectionRule id="ov-state" label="Module state" meta={data.modules.length} />
        <StateBar className="mt-3" parts={parts} label="Module state" />
      </section>

      <section aria-labelledby="ov-server">
        <SectionRule id="ov-server" label="Server" />
        {g ? (
          <>
            <dl className="mt-1.5">
              <Fact label="Members">{g.member_count.toLocaleString()}</Fact>
              <Fact label="Roles">{g.role_count.toLocaleString()}</Fact>
              <Fact label="Channels">{g.channel_count.toLocaleString()}</Fact>
              {data.prefix && (
                <Fact label="Command prefix">
                  <span dir="ltr">{data.prefix}</span>
                </Fact>
              )}
            </dl>
            {data.channels && data.channels.length > 0 && (
              <MicroBars
                className="mt-3"
                label="Channels by type"
                rows={data.channels.map((c) => ({ key: c.kind, label: c.label, value: c.count }))}
              />
            )}
          </>
        ) : (
          <p className="mt-2 text-body text-fg-2">{data.guildError ?? "Server details unavailable."}</p>
        )}
      </section>

      <section aria-labelledby="ov-access">
        <SectionRule id="ov-access" label="Your access" />
        <dl className="mt-1.5">
          <Fact label="Role">
            <span className="font-sans">{data.accessLabel}</span>
          </Fact>
          {data.grantsCount != null && <Fact label="Active grants">{data.grantsCount}</Fact>}
        </dl>
      </section>
    </div>
  );
}
