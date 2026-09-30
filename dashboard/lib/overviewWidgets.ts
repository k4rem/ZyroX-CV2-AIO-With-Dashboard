/**
 * Overview activity band (Phase 1.6 AD §6, RP §1.2). Pure — covered by node --test.
 *
 * Widgets are registered here by the phase that ships their data source (Tickets V2,
 * Security events, Logging history, audit read API). A widget renders only when the
 * loader reports its source as available; with nothing available the band renders
 * nothing at all — no frame, no placeholder.
 */

export type ActivitySource = "tickets.activity" | "security.events" | "logging.volume" | "audit.recent";

export interface ActivityWidgetDef {
  id: string;
  source: ActivitySource;
  title: string;
}

/** Empty until a later phase provides a real source. */
export const ACTIVITY_WIDGETS: readonly ActivityWidgetDef[] = [];

export function availableActivityWidgets(
  available: ReadonlySet<ActivitySource>,
  registry: readonly ActivityWidgetDef[] = ACTIVITY_WIDGETS,
): ActivityWidgetDef[] {
  return registry.filter((w) => available.has(w.source));
}
