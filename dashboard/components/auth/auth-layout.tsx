import * as React from "react";
import Link from "next/link";
import { LatticeBackground } from "@/components/brand/lattice-background";
import { PerimeterMark } from "@/components/brand/perimeter-mark";
import { Wordmark } from "@/components/brand/wordmark";
import { cn } from "@/lib/utils";

export function AuthLayout({
  title,
  children,
  actions,
  perimeterOpen,
}: {
  title: string;
  children: React.ReactNode;
  actions?: React.ReactNode;
  /** Inner ring opening animation on continue route */
  perimeterOpen?: boolean;
}) {
  return (
    <div className="cls-gateway relative flex min-h-[100svh] flex-col bg-void text-fg-1">
      <LatticeBackground />
      <header className="relative z-10 mx-auto flex h-topbar w-full max-w-lg items-center px-4 md:px-6">
        <Link href="/" className="rounded-sm focus-visible:outline-none">
          <Wordmark markHeight={20} />
        </Link>
      </header>
      <main className="relative z-10 flex flex-1 flex-col items-center justify-center px-4 pb-16 pt-6">
        <div className="w-full max-w-[400px] text-center">
          <div className={cn("mx-auto mb-6 flex justify-center", perimeterOpen && "cls-perimeter-open")}>
            <PerimeterMark variant="auth" showLabels={false} />
          </div>
          <h1 className="cls-auth-title text-fg-1">{title}</h1>
          <div className="mt-4 text-start text-body-prose text-fg-2">{children}</div>
          {actions ? <div className="mt-6 flex flex-col gap-2 sm:flex-row sm:justify-center">{actions}</div> : null}
        </div>
      </main>
    </div>
  );
}
