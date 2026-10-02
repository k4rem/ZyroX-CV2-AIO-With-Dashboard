"use client";

import * as React from "react";
import Link from "next/link";
import { cn } from "@/lib/utils";
import { Wordmark } from "@/components/brand/wordmark";
import { SignInButton } from "@/components/landing/sign-in-button";

export function LandingNav({ onSignInLock }: { onSignInLock?: () => void }) {
  const [scrolled, setScrolled] = React.useState(false);

  React.useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 24);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  return (
    <header
      className={cn(
        "sticky top-0 z-30 min-h-topbar border-b transition-[background-color,backdrop-filter,border-color] duration-standard",
        scrolled ? "border-line bg-chrome/80 backdrop-blur-md" : "border-transparent bg-transparent",
      )}
    >
      <div className="cls-public-container flex h-topbar items-center justify-between gap-4">
        <Link
          href="/"
          className="rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 focus-visible:ring-offset-2 focus-visible:ring-offset-void"
        >
          <Wordmark markHeight={28} />
        </Link>
        <SignInButton emphasis="nav" onLock={onSignInLock} />
      </div>
    </header>
  );
}
