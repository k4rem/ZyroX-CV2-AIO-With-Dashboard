import * as React from "react";
import type { OverviewPayload } from "@/lib/loadOverview";
import type { ActivitySource } from "@/lib/overviewWidgets";
import { PageHeader } from "@/components/dashboard/page-header";
import { ReadoutRail } from "./readout-rail";
import { AttentionQueue } from "./attention-queue";
import { ModuleMatrix } from "./module-matrix";
import { FactsColumn } from "./facts-column";
import { ActivityBand } from "./activity-band";

const enter = (i: number) => ({ "--i": i }) as React.CSSProperties;

/** No activity source exists before Tickets V2 / Security events ship. */
const NO_SOURCES: ReadonlySet<ActivitySource> = new Set();

/**
 * Overview — Operations Deck (Phase 1.6 RP §1). Readout rail, then the attention
 * queue and module matrix in the main column, with facts at inline-end on wide
 * screens. Every value is live; anything without a source is not rendered.
 */
export function OverviewContent({ data }: { data: OverviewPayload; guildId: string }) {
  return (
    <div className="space-y-8">
      <PageHeader title="Overview" description="Live configuration and health for this server." className="mb-0" />

      <ReadoutRail data={data} className="cls-enter" style={enter(0)} />

      <div className="grid gap-x-10 gap-y-8 xl:grid-cols-[minmax(0,1fr)_20rem] 3xl:grid-cols-[minmax(0,1fr)_24rem]">
        <div className="min-w-0 space-y-8">
          <AttentionQueue items={data.attention} className="cls-enter" style={enter(1)} />
          <ModuleMatrix modules={data.modules} className="cls-enter" style={enter(2)} />
        </div>
        <FactsColumn data={data} className="cls-enter" style={enter(3)} />
      </div>

      <ActivityBand sources={NO_SOURCES} />
    </div>
  );
}
