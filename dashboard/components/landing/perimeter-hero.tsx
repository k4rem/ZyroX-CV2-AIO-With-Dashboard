"use client";

import * as React from "react";
import { PerimeterMark, type PerimeterDomain } from "@/components/brand/perimeter-mark";
import { SignInButton } from "@/components/landing/sign-in-button";

export function PerimeterHero({
  locked,
  onLock,
  activeDomain,
}: {
  locked: boolean;
  onLock: () => void;
  activeDomain: PerimeterDomain | null;
}) {
  return (
    <section className="cls-public-container relative grid w-full gap-8 pb-10 pt-6 md:grid-cols-12 md:items-center md:gap-10 md:pb-16 md:pt-12 lg:pt-14">
      <div className="order-2 flex flex-col gap-6 md:order-1 md:col-span-5 cls-gateway-reveal">
        <h1 className="cls-display-hero text-balance text-fg-1">Private control for CLS Discord.</h1>
        <p className="cls-lead max-w-[52ch] text-fg-2">
          Security, moderation, support, recovery, and automation, managed in one place. Every dashboard change is
          recorded.
        </p>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <SignInButton onLock={onLock} className="w-full sm:w-auto" />
          <p className="text-small text-fg-3">Invite-only. Access is granted by the CLS owner.</p>
        </div>
      </div>

      <div className="order-1 min-w-0 md:order-2 md:col-span-7 md:pe-2 lg:pe-4">
        <PerimeterMark variant="hero" locked={locked} activeDomain={activeDomain} parallax showLabels />
      </div>
    </section>
  );
}
