"use client";

import * as React from "react";
import type { ChannelKind } from "@/lib/overviewModel";
import { cn } from "@/lib/utils";

const INK: Record<ChannelKind, string> = {
  text: "bg-fg-2",
  voice: "bg-chart-2",
  category: "bg-fg-4",
  other: "bg-neutral/50",
};

/** Above this many channels individual ticks get too thin; draw proportional runs instead. */
const MAX_TICKS = 96;

/**
 * Server composition (Task A.1): one slanted tick per real channel, grouped by
 * Discord channel type. A linear counterpoint to the two rings.
 */
export function ChannelComposition({
  groups,
  total,
}: {
  groups: { kind: ChannelKind; label: string; count: number }[] | null;
  total: number | null;
}) {
  const [active, setActive] = React.useState<ChannelKind | null>(null);
  const counted = groups?.reduce((n, g) => n + g.count, 0) ?? 0;
  const ticks = counted > 0 && counted <= MAX_TICKS;
  const summary = groups?.map((g) => `${g.label} ${g.count}`).join(", ") ?? "";

  return (
    <div className="flex h-full flex-col gap-4 p-5">
      <div className="flex items-baseline justify-between gap-3">
        <h3 className="text-panel-title text-fg-1">Server composition</h3>
        {total != null && (
          <span className="font-mono text-small tabular-nums text-fg-3" dir="auto">
            {total} channels
          </span>
        )}
      </div>

      {!groups || counted === 0 ? (
        <p className="text-small text-fg-3">Channel list unavailable.</p>
      ) : (
        <>
          <div
            role="img"
            aria-label={`Channels by type: ${summary}`}
            className="flex h-9 items-stretch gap-[2px] px-1"
          >
            {groups.map((g, gi) =>
              ticks ? (
                <span
                  key={g.kind}
                  title={`${g.label} — ${g.count} channels`}
                  onMouseEnter={() => setActive(g.kind)}
                  onMouseLeave={() => setActive(null)}
                  className={cn("flex min-w-0 gap-[2px]", gi > 0 && "ms-1.5")}
                  style={{ flexGrow: g.count, flexBasis: 0 }}
                >
                  {Array.from({ length: g.count }, (_, i) => (
                    <span
                      key={i}
                      className={cn(
                        "cls-arc min-w-px flex-1 -skew-x-[30deg] transition-opacity",
                        INK[g.kind],
                        active && active !== g.kind && "opacity-30",
                      )}
                      style={{ "--i": Math.min(i, 24) } as React.CSSProperties}
                    />
                  ))}
                </span>
              ) : (
                <span
                  key={g.kind}
                  title={`${g.label} — ${g.count} channels`}
                  onMouseEnter={() => setActive(g.kind)}
                  onMouseLeave={() => setActive(null)}
                  className={cn("cls-arc -skew-x-[30deg]", INK[g.kind], active && active !== g.kind && "opacity-30")}
                  style={{ flexGrow: g.count, flexBasis: 0 }}
                />
              ),
            )}
          </div>
          <ul className="grid grid-cols-2 gap-x-4 gap-y-0.5 2xl:grid-cols-3">
            {groups.map((g) => (
              <li
                key={g.kind}
                tabIndex={0}
                onMouseEnter={() => setActive(g.kind)}
                onMouseLeave={() => setActive(null)}
                onFocus={() => setActive(g.kind)}
                onBlur={() => setActive(null)}
                className={cn(
                  "-mx-1 flex items-center gap-2 rounded-xs px-1 py-1 text-small transition-colors duration-micro",
                  active === g.kind ? "bg-surface-2 text-fg-1" : "text-fg-2",
                )}
              >
                <span aria-hidden="true" className={cn("h-2 w-1.5 shrink-0 -skew-x-[30deg] rtl:skew-x-[30deg]", INK[g.kind])} />
                <span className="truncate">{g.label}</span>
                <span className="ms-auto font-mono tabular-nums text-fg-1">{g.count}</span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}
