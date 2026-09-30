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
      <div className="mx-auto flex h-topbar max-w-6xl items-center justify-between gap-4 px-4 md:px-6">
        <Link href="/" className="flex items-center gap-2 rounded-sm focus-visible:outline-none">
          <Wordmark markHeight={20} />
        </Link>
        <div className="hidden sm:block">
          <SignInButton onLock={onSignInLock} />
        </div>
      </div>
    </header>
  );
}
