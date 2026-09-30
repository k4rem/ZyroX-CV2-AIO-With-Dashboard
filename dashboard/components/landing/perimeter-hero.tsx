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
    <section className="relative mx-auto grid w-full max-w-6xl gap-10 px-4 pb-10 pt-6 md:grid-cols-12 md:items-center md:gap-8 md:px-6 md:pb-16 md:pt-10">
      <div className="order-2 flex flex-col gap-6 md:order-1 md:col-span-5 cls-gateway-reveal">
        <div>
          <p className="cls-overline mb-3 text-brand-400/90">CLS OS</p>
          <h1 className="cls-display-hero text-balance text-fg-1">Private control for CLS Discord.</h1>
        </div>
        <p className="cls-lead max-w-[52ch] text-fg-2">
          Security, support, recovery, and automation run from one operations perimeter. Access is granted by
          the CLS root owner—not sold on a storefront.
        </p>
        <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
          <SignInButton onLock={onLock} className="w-full sm:w-auto" />
          <p className="text-small text-fg-3">Access is invite-only.</p>
        </div>
      </div>

      <div
        className="order-1 md:order-2 md:col-span-7 cls-perimeter-scroll-parallax"
        aria-hidden={false}
      >
        <PerimeterMark
          variant="hero"
          locked={locked}
          activeDomain={activeDomain}
          parallax
          showLabels
          className="max-md:max-h-[280px] max-md:max-w-[280px]"
        />
      </div>
    </section>
  );
}
