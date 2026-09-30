"use client";

import * as React from "react";
import {
  History,
  LifeBuoy,
  RotateCcw,
  ShieldAlert,
  Workflow,
  Gavel,
  type LucideIcon,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { PerimeterDomain } from "@/components/brand/perimeter-mark";

const DOMAINS: {
  id: PerimeterDomain;
  name: string;
  line: string;
  availability: string;
  icon: LucideIcon;
}[] = [
  {
    id: "Security",
    name: "Security",
    line: "Antinuke protects the server from destructive changes.",
    availability: "Available now",
    icon: ShieldAlert,
  },
  {
    id: "Support",
    name: "Support",
    line: "Ticket categories and panels configured from the dashboard; tickets run in Discord.",
    availability: "Available now (V2 builder in development)",
    icon: LifeBuoy,
  },
  {
    id: "Recovery",
    name: "Recovery",
    line: "Encrypted backups of bot and platform data. Restore tooling is being built and tested.",
    availability: "In development",
    icon: RotateCcw,
  },
  {
    id: "Automation",
    name: "Automation",
    line: "Welcome messages, auto roles, reaction roles, and Join to Create voice channels.",
    availability: "Available now",
    icon: Workflow,
  },
  {
    id: "Moderation",
    name: "Moderation",
    line: "Automod rules and event logging to channels you choose.",
    availability: "Available now",
    icon: Gavel,
  },
  {
    id: "Audit",
    name: "Audit",
    line: "Every dashboard change is recorded with who made it and when.",
    availability: "Available now (viewer in development)",
    icon: History,
  },
];

export function DomainList({
  activeDomain,
  onActiveDomain,
}: {
  activeDomain: PerimeterDomain | null;
  onActiveDomain: (d: PerimeterDomain | null) => void;
}) {
  return (
    <section id="inside-cls-os" className="cls-public-container pb-16">
      <p className="cls-overline mb-6 text-fg-3">What runs inside</p>
      <ul className="grid grid-cols-1 border-y border-line-subtle md:grid-cols-2">
        {DOMAINS.map((d, index) => {
          const Icon = d.icon;
          return (
            <li
              key={d.id}
              className={cn(
                "border-line-subtle",
                index < 4 && "border-b",
                index % 2 === 0 && "md:border-e md:pe-6",
                index % 2 === 1 && "md:ps-6",
                index >= 2 && "md:border-t",
              )}
              onMouseEnter={() => onActiveDomain(d.id)}
              onMouseLeave={() => onActiveDomain(null)}
              onFocus={() => onActiveDomain(d.id)}
              onBlur={() => onActiveDomain(null)}
            >
              <div
                tabIndex={0}
                className={cn(
                  "flex gap-4 py-4 text-start outline-none transition-colors duration-micro",
                  "hover:bg-surface-1/50 focus-visible:bg-surface-1/50 focus-visible:ring-2 focus-visible:ring-inset focus-visible:ring-brand-400",
                )}
              >
                <Icon className="mt-0.5 size-5 shrink-0 text-fg-3" strokeWidth={1.5} aria-hidden="true" />
                <div className="min-w-0 flex-1">
                  <p className="text-section text-fg-1">{d.name}</p>
                  <p className="mt-1 text-body-prose text-fg-2">{d.line}</p>
                  <p className="mt-2 text-caption text-fg-3">{d.availability}</p>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
