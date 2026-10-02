"use client";

import { PerimeterMark, type PerimeterDomain } from "@/components/brand/perimeter-mark";
import { SignInButton } from "@/components/landing/sign-in-button";
import { useLandingDepth } from "@/components/landing/use-parallax";

export function PerimeterHero({
  locked,
  onLock,
  activeDomain,
}: {
  locked: boolean;
  onLock: () => void;
  activeDomain: PerimeterDomain | null;
}) {
  const ref = useLandingDepth<HTMLElement>();

  return (
    <section ref={ref} className="cls-hero relative">
      <div className="cls-hero-glow pointer-events-none absolute inset-0" aria-hidden="true" />
      <div className="cls-hero-settle cls-public-container relative z-[1] grid w-full gap-8 pb-10 pt-6 md:grid-cols-12 md:items-center md:gap-10 md:pb-16 md:pt-12 lg:pt-14">
        <div className="order-2 flex flex-col gap-6 md:order-1 md:col-span-5">
          <div className="cls-enter" style={{ ["--i" as string]: 0 }}>
            <h1 className="cls-depth-ui text-balance text-fg-1 cls-display-hero">Private control for CLS Discord.</h1>
          </div>
          <div className="cls-enter" style={{ ["--i" as string]: 1 }}>
            <p className="cls-depth-mid cls-lead max-w-[52ch] text-fg-2">
              Security, moderation, support, recovery, and automation, managed in one place. Every dashboard change is
              recorded.
            </p>
          </div>
          <div className="cls-enter" style={{ ["--i" as string]: 2 }}>
            <div className="cls-depth-fg flex flex-col items-start gap-3">
              <SignInButton onLock={onLock} className="w-full sm:w-auto" />
              <p className="text-small text-fg-3">Invite-only. Access is granted by the CLS owner.</p>
            </div>
          </div>
        </div>

        <div className="cls-enter order-1 min-w-0 md:order-2 md:col-span-7 md:pe-2 lg:pe-4" style={{ ["--i" as string]: 3 }}>
          <div className="cls-hero-visual">
            <PerimeterMark variant="hero" locked={locked} activeDomain={activeDomain} parallax showLabels />
          </div>
        </div>
      </div>
    </section>
  );
}
