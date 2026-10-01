import * as React from "react";
import type { OverviewPayload } from "@/lib/loadOverview";
import { cn } from "@/lib/utils";
import { SystemCore } from "./instruments/system-core";
import { ModuleStateRing } from "./instruments/module-state-ring";
import { ChannelComposition } from "./instruments/channel-composition";
import { LatencySparkline } from "./instruments/latency-sparkline";

/**
 * Instrument deck (Phase 1.6 Task A.1): the Overview's focal region. One stage,
 * hairline-separated regions — not a card per chart. Every instrument encodes a
 * live reading; future Security / Tickets / Logging instruments get a region
 * here only once their sources exist (see overviewWidgets).
 *
 * Order on narrow screens: core → live latency → module state → composition.
 */
export function AnalyticsDeck({ data, className, style }: { data: OverviewPayload; className?: string; style?: React.CSSProperties }) {
  return (
    <section aria-labelledby="ov-deck" className={className} style={style}>
      <h2 id="ov-deck" className="sr-only">
        Instruments
      </h2>
      <div
        className={cn(
          "cls-cut cls-signal-edge grid gap-px overflow-hidden rounded-md border border-line bg-line-subtle shadow-hl-1 [&>*]:bg-void",
          "md:grid-cols-2",
          "xl:grid-cols-[minmax(0,1.35fr)_minmax(0,1fr)]",
          "3xl:grid-cols-[minmax(0,1.25fr)_minmax(0,1fr)_minmax(0,1fr)]",
        )}
      >
        <div className="order-1 md:col-span-2 xl:col-span-1 xl:row-span-2">
          <SystemCore
            modules={data.coreModules}
            permissions={data.corePermissions}
            initialLevel={data.healthLevel}
            initialOnline={data.botOnline}
            initialLatencyMs={data.botLatencyMs}
          />
        </div>
        <div className="order-3 md:order-2">
          <ModuleStateRing modules={data.modules} />
        </div>
        <div className="order-4 md:order-3">
          <ChannelComposition groups={data.channels} total={data.guild?.channel_count ?? null} />
        </div>
        <div className="order-2 md:order-4 md:col-span-2 3xl:col-start-2">
          <LatencySparkline initialLatencyMs={data.botLatencyMs} />
        </div>
      </div>
    </section>
  );
}
