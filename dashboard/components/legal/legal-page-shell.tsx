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
        <div className="mx-auto flex h-topbar max-w-3xl items-center justify-between px-4 md:px-6">
          <Link href="/" className="rounded-sm focus-visible:outline-none">
            <Wordmark markHeight={20} />
          </Link>
          <Link href="/" className="text-small text-brand-400 hover:underline">
            Back to sign in
          </Link>
        </div>
      </header>
      <main className="relative z-10 mx-auto max-w-3xl px-4 py-10 md:px-6 md:py-14">
        <h1 className="cls-auth-title text-fg-1">{title}</h1>
        <div className="prose-cls mt-8 space-y-6 text-body-prose text-fg-2">{children}</div>
        <p className="mt-10 text-caption text-fg-3">
          Draft for operator review. This is not legal advice and does not describe certifications or compliance
          guarantees.
        </p>
      </main>
      <LandingFooter />
    </div>
  );
}
