import * as React from "react";
import Link from "next/link";
import { ChevronRight, CircleCheck, Info, OctagonAlert, TriangleAlert, type LucideIcon } from "lucide-react";
import type { AttentionItem, AttentionSeverity } from "@/lib/deriveAttention";
import { SectionRule } from "@/components/ui/section-rule";
import { cn } from "@/lib/utils";

const SEVERITY: Record<AttentionSeverity, { glyph: LucideIcon; tone: string; label: string }> = {
  critical: { glyph: OctagonAlert, tone: "text-danger", label: "Critical" },
  warning: { glyph: TriangleAlert, tone: "text-warn", label: "Warning" },
  info: { glyph: Info, tone: "text-info", label: "Notice" },
};

/**
 * Attention queue (RP §1.1): what needs a decision, most severe first. Rows on the
 * canvas separated by hairlines; each goes straight to the page that fixes it.
 */
export function AttentionQueue({
  items,
  className,
  style,
}: {
  items: AttentionItem[];
  className?: string;
  style?: React.CSSProperties;
}) {
  return (
    <section aria-labelledby="ov-attention" className={className} style={style}>
      <SectionRule id="ov-attention" label="Needs attention" meta={items.length > 0 ? items.length : undefined} />
      {items.length === 0 ? (
        <p className="mt-3 flex items-center gap-2 text-body text-fg-2">
          <CircleCheck className="size-4 shrink-0 text-ok" strokeWidth={1.75} aria-hidden="true" />
          Nothing needs attention.
          <span className="text-fg-3">Required modules, permissions, Antinuke, Logging and Tickets were checked.</span>
        </p>
      ) : (
        <ol className="mt-2 border-t border-line-subtle">
          {items.map((item) => {
            const s = SEVERITY[item.severity];
            const Glyph = s.glyph;
            return (
              <li key={item.id} className="border-b border-line-subtle">
                <Link
                  href={item.href}
                  className="cls-row group grid grid-cols-[1rem_minmax(0,1fr)] items-start gap-x-3 gap-y-1 px-2 py-2.5 hover:bg-surface-2 focus-visible:bg-surface-2 sm:grid-cols-[1rem_minmax(0,1fr)_auto] sm:items-center"
                >
                  <Glyph className={cn("mt-0.5 size-4 sm:mt-0", s.tone)} strokeWidth={1.75} aria-hidden="true" />
                  <span className="min-w-0">
                    <span className="sr-only">{s.label}: </span>
                    <span className="text-body text-fg-1" dir="auto">
                      {item.message}
                    </span>
                    <span className="ms-2 whitespace-nowrap font-mono text-caption text-fg-3">{item.origin}</span>
                  </span>
                  <span className="col-start-2 inline-flex items-center gap-1 text-small text-fg-3 transition-colors duration-micro group-hover:text-brand-300 sm:col-start-3">
                    Open {item.origin}
                    <span className="cls-row-go inline-flex" aria-hidden="true">
                      <ChevronRight className="cls-mirror size-3.5" />
                    </span>
                  </span>
                </Link>
              </li>
            );
          })}
        </ol>
      )}
    </section>
  );
}
