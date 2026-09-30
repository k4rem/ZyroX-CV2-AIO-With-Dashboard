import * as React from "react";
import { availableActivityWidgets, type ActivitySource } from "@/lib/overviewWidgets";

/**
 * Activity band (AD §6): time-series and event widgets from later phases mount here.
 * With no available source it renders nothing — no frame, heading or placeholder.
 */
export function ActivityBand({ sources }: { sources: ReadonlySet<ActivitySource> }) {
  const widgets = availableActivityWidgets(sources);
  if (widgets.length === 0) return null;
  return (
    <section aria-label="Activity" className="grid gap-8 xl:grid-cols-2">
      {widgets.map((w) => (
        <div key={w.id} data-widget={w.id} />
      ))}
    </section>
  );
}
