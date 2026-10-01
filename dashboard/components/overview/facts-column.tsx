import * as React from "react";
import type { OverviewPayload } from "@/lib/loadOverview";
import { SectionRule } from "@/components/ui/section-rule";
import { cn } from "@/lib/utils";

function Fact({ label, children }: { label: string; children: React.ReactNode }) {
  return (
    <div className="flex items-baseline justify-between gap-4 border-b border-line-subtle py-1.5 last:border-b-0">
      <dt className="text-small text-fg-2">{label}</dt>
      <dd className="min-w-0 truncate text-end font-mono text-body tabular-nums text-fg-1">{children}</dd>
    </div>
  );
}

/** Facts column (RP §1.1): plain facts — no statuses to act on here. Composition lives in the instrument deck. */
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

  return (
    <div className={cn("grid content-start gap-x-8 gap-y-7 md:grid-cols-2 xl:grid-cols-1", className)} style={style}>
      <section aria-labelledby="ov-server">
        <SectionRule id="ov-server" label="Server" />
        {g ? (
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
