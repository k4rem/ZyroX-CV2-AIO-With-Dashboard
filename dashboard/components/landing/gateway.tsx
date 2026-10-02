"use client";

import * as React from "react";
import { LatticeBackground } from "@/components/brand/lattice-background";
import type { PerimeterDomain } from "@/components/brand/perimeter-mark";
import { DomainList } from "@/components/landing/domain-list";
import { LandingFooter } from "@/components/landing/landing-footer";
import { LandingNav } from "@/components/landing/landing-nav";
import { NoticeBar } from "@/components/landing/notice-bar";
import { PerimeterHero } from "@/components/landing/perimeter-hero";
import { HERO_CYCLE_MS, heroShouldAdvance } from "@/lib/landingMotion";
import { neighborDomain } from "@/lib/landingDomains";

export function Gateway({ notice }: { notice?: string | null }) {
  const [locked, setLocked] = React.useState(false);
  const [heroDomain, setHeroDomain] = React.useState<PerimeterDomain>("Security");
  const held = React.useRef(false);

  React.useEffect(() => {
    const media = window.matchMedia("(prefers-reduced-motion: reduce)");
    const tick = () => {
      if (!heroShouldAdvance({ reduce: media.matches, paused: held.current })) return;
      setHeroDomain((current) => neighborDomain(current, 1));
    };
    const id = window.setInterval(tick, HERO_CYCLE_MS);
    return () => window.clearInterval(id);
  }, []);

  return (
    <div className="cls-gateway relative min-h-[100svh] overflow-x-clip bg-void text-fg-1">
      <LatticeBackground />
      <NoticeBar notice={notice} />
      <LandingNav onSignInLock={() => setLocked(true)} />
      <main>
        <PerimeterHero
          locked={locked}
          onLock={() => setLocked(true)}
          activeDomain={heroDomain}
          onDomainSelect={setHeroDomain}
          onHoldChange={(next) => {
            held.current = next;
          }}
        />
        <DomainList />
      </main>
      <LandingFooter />
    </div>
  );
}
