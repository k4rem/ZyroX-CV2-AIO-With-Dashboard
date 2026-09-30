"use client";

import * as React from "react";
import { LatticeBackground } from "@/components/brand/lattice-background";
import type { PerimeterDomain } from "@/components/brand/perimeter-mark";
import { DomainList } from "@/components/landing/domain-list";
import { LandingFooter } from "@/components/landing/landing-footer";
import { LandingNav } from "@/components/landing/landing-nav";
import { NoticeBar } from "@/components/landing/notice-bar";
import { PerimeterHero } from "@/components/landing/perimeter-hero";

export function Gateway({ notice }: { notice?: string | null }) {
  const [locked, setLocked] = React.useState(false);
  const [activeDomain, setActiveDomain] = React.useState<PerimeterDomain | null>(null);

  return (
    <div className="cls-gateway relative min-h-[100svh] bg-void text-fg-1">
      <LatticeBackground />
      <NoticeBar notice={notice} />
      <LandingNav onSignInLock={() => setLocked(true)} />
      <main>
        <PerimeterHero locked={locked} onLock={() => setLocked(true)} activeDomain={activeDomain} />
        <DomainList activeDomain={activeDomain} onActiveDomain={setActiveDomain} />
      </main>
      <LandingFooter />
    </div>
  );
}
