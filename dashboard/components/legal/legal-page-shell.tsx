import * as React from "react";
import Link from "next/link";
import { LatticeBackground } from "@/components/brand/lattice-background";
import { Wordmark } from "@/components/brand/wordmark";
import { LandingFooter } from "@/components/landing/landing-footer";

export function LegalPageShell({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="cls-gateway relative min-h-[100svh] bg-void text-fg-1">
      <LatticeBackground />
      <header className="relative z-10 border-b border-line-subtle bg-chrome/60 backdrop-blur-md">
        <div className="cls-public-container flex h-topbar items-center justify-between gap-4">
          <Link
            href="/"
            className="rounded-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 focus-visible:ring-offset-2 focus-visible:ring-offset-void"
          >
            <Wordmark markHeight={28} />
          </Link>
          <Link
            href="/"
            className="inline-flex min-h-11 items-center text-small text-brand-400 hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-brand-400 focus-visible:ring-offset-2 focus-visible:ring-offset-void rounded-sm px-1"
          >
            Back to sign in
          </Link>
        </div>
      </header>
      <main className="cls-public-container relative z-10 max-w-3xl py-10 md:py-14">
        <h1 className="cls-auth-title text-fg-1">{title}</h1>
        <div className="mt-8 space-y-8 text-body-prose text-fg-2">{children}</div>
        <p className="mt-10 text-caption text-fg-3">
          Draft for operator review. This is not legal advice and does not describe certifications or compliance
          guarantees.
        </p>
      </main>
      <LandingFooter />
    </div>
  );
}
