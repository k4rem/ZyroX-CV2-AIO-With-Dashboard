"use client";

import * as React from "react";
import { LifeBuoy, MessageSquare, ScrollText, ShieldAlert, UserRound, Workflow, type LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { LANDING_DOMAINS, landingDomain, neighborDomain, type PerimeterDomain } from "@/lib/landingDomains";

const ICONS: Record<PerimeterDomain, LucideIcon> = {
  Security: ShieldAlert,
  Tickets: LifeBuoy,
  Logging: ScrollText,
  Messaging: MessageSquare,
  Roles: UserRound,
  Automation: Workflow,
};

export function DomainList({
  activeDomain,
  onActiveDomain,
}: {
  activeDomain: PerimeterDomain;
  onActiveDomain: (domain: PerimeterDomain) => void;
}) {
  const sectionRef = React.useRef<HTMLElement>(null);
  const [risen, setRisen] = React.useState(false);
  const buttons = React.useRef<Record<string, HTMLButtonElement | null>>({});
  const domain = landingDomain(activeDomain);

  React.useEffect(() => {
    const el = sectionRef.current;
    if (!el) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (reduce) return;
    const observer = new IntersectionObserver(
      (entries) => {
        if (entries[0]?.isIntersecting) {
          setRisen(true);
          observer.disconnect();
        }
      },
      { threshold: 0.2 },
    );
    observer.observe(el);
    return () => observer.disconnect();
  }, []);

  function onKeyDown(event: React.KeyboardEvent<HTMLDivElement>) {
    if (event.key !== "ArrowDown" && event.key !== "ArrowUp" && event.key !== "Home" && event.key !== "End") return;
    event.preventDefault();
    const next =
      event.key === "Home"
        ? LANDING_DOMAINS[0].id
        : event.key === "End"
          ? LANDING_DOMAINS[LANDING_DOMAINS.length - 1].id
          : neighborDomain(activeDomain, event.key === "ArrowDown" ? 1 : -1);
    onActiveDomain(next);
    buttons.current[next]?.focus();
  }

  return (
    <section id="inside-cls-os" ref={sectionRef} className={cn("cls-public-container border-t border-line-subtle pb-16 pt-10", risen && "cls-domain-rise")}>
      <h2 className="cls-overline mb-6 text-fg-3">What runs inside</h2>
      <div className="grid grid-cols-1 items-start gap-6 lg:grid-cols-[minmax(16rem,22rem)_minmax(0,1fr)]">
        <div role="tablist" aria-label="What runs inside" aria-orientation="vertical" className="flex flex-col gap-1" onKeyDown={onKeyDown}>
          {LANDING_DOMAINS.map((item) => {
            const Icon = ICONS[item.id];
            const selected = item.id === activeDomain;
            return (
              <button
                key={item.id}
                ref={(node) => {
                  buttons.current[item.id] = node;
                }}
                type="button"
                role="tab"
                id={`domain-tab-${item.id}`}
                aria-selected={selected}
                aria-controls="domain-detail"
                tabIndex={selected ? 0 : -1}
                className={cn(
                  "flex w-full items-start gap-3 rounded-sm px-3 py-3 text-start outline-none transition-colors duration-micro",
                  "focus-visible:ring-2 focus-visible:ring-brand-400 focus-visible:ring-offset-2 focus-visible:ring-offset-void",
                  selected ? "bg-surface-2 text-fg-1 ring-1 ring-inset ring-brand-400/40" : "text-fg-2 hover:bg-surface-1 hover:text-fg-1",
                )}
                onPointerEnter={(event) => {
                  if (event.pointerType === "mouse") onActiveDomain(item.id);
                }}
                onFocus={() => onActiveDomain(item.id)}
                onClick={() => onActiveDomain(item.id)}
              >
                <Icon className={cn("mt-0.5 size-4 shrink-0", selected ? "text-brand-400" : "text-fg-3")} strokeWidth={1.5} aria-hidden="true" />
                <span className="min-w-0">
                  <span className="block text-body font-medium text-fg-1">{item.name}</span>
                  <span className="mt-1 block text-small text-fg-3">{item.hint}</span>
                </span>
              </button>
            );
          })}
        </div>

        <div
          role="tabpanel"
          id="domain-detail"
          aria-labelledby={`domain-tab-${domain.id}`}
          className="min-w-0 rounded-sm border border-line bg-surface-1 p-4 sm:p-5"
        >
          <p className="text-section text-fg-1">{domain.name}</p>
          <p className="mt-2 max-w-[62ch] text-body text-fg-2">{domain.summary}</p>
          <div className="mt-4 overflow-hidden rounded-sm border border-line bg-void">
            <div className="border-b border-line-subtle px-3 py-2 text-caption text-fg-3">{domain.name}</div>
            <ul>
              {domain.capabilities.map((row) => (
                <li key={row} className="border-b border-line-subtle px-3 py-2.5 text-small text-fg-1 last:border-b-0">
                  {row}
                </li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}
