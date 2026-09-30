/**
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║                                                                  ║
 * ║   ░█▀▀░█▀█░█▀▄░█▀▀░█░█   ░█▀▄░█▀▀░█░█░█▀▀                     ║
 * ║   ░█░░░█░█░█░█░█▀▀░▄▀▄   ░█░█░█▀▀░▀▄▀░▀▀█                     ║
 * ║   ░▀▀▀░▀▀▀░▀▀░░▀▀▀░▀░▀   ░▀▀░░▀▀▀░░▀░░▀▀▀                     ║
 * ║                                                                  ║
 * ║           © 2026 CodeX Devs — All Rights Reserved               ║
 * ║                                                                  ║
 * ║   discord  ──  https://discord.gg/codexdev                      ║
 * ║   youtube  ──  https://youtube.com/@CodeXDevs                   ║
 * ║   github   ──  https://github.com/RayExo                        ║
 * ║                                                                  ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

import React from "react";
import { cn } from "@/lib/utils";

interface PageHeaderProps {
  title: string;
  description?: string;
  children?: React.ReactNode;
  icon?: React.ElementType;
  className?: string;
}

/**
 * Page header v2 (AD §4): start-aligned title and one-line description, factual
 * context or actions at inline-end, closed by the engraved rule that starts with
 * the signal tick. No icon tiles, eyebrows, gradients or glow.
 * `icon` is accepted for legacy callers and rendered as a quiet 20 px glyph.
 */
export const PageHeader = ({ title, description, children, icon: Icon, className }: PageHeaderProps) => {
  return (
    <header className={cn("mb-6", className)}>
      <div className="flex flex-col justify-between gap-3 md:flex-row md:items-end">
        <div className="min-w-0">
          <h1 className="flex items-center gap-2 text-page-title text-fg-1">
            {Icon && <Icon className="size-5 shrink-0 text-fg-2" strokeWidth={1.5} aria-hidden="true" />}
            <span className="truncate">{title}</span>
          </h1>
          {description && <p className="mt-0.5 max-w-[80ch] text-body text-fg-2">{description}</p>}
        </div>
        {children && <div className="flex shrink-0 flex-wrap items-center gap-2">{children}</div>}
      </div>
      <div aria-hidden="true" className="mt-3 flex items-center">
        <span className="cls-tick" />
        <span className="h-px flex-1 bg-line-subtle" />
      </div>
    </header>
  );
};
