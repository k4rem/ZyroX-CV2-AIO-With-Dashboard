import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Faint 30° isometric grid (DS §9.5). Decorative only; masked so it never competes with content.
 */
export function LatticeBackground({ className }: { className?: string }) {
  return (
    <div
      aria-hidden="true"
      className={cn(
        "pointer-events-none absolute inset-0 overflow-hidden opacity-0 cls-lattice-fade",
        className,
      )}
    >
      <svg className="absolute inset-0 h-full w-full text-fg-3/15" preserveAspectRatio="xMidYMid slice">
        <defs>
          <pattern
            id="cls-lattice"
            width="40"
            height="69.28"
            patternUnits="userSpaceOnUse"
            patternTransform="scale(1.15)"
          >
            <path d="M0 34.64 L20 0 L40 0 L20 34.64 Z" fill="none" stroke="currentColor" strokeWidth="0.45" />
            <path d="M0 34.64 L20 69.28 L40 69.28 L20 34.64 Z" fill="none" stroke="currentColor" strokeWidth="0.45" />
          </pattern>
          <radialGradient id="cls-lattice-mask" cx="50%" cy="45%" r="65%">
            <stop offset="0%" stopColor="white" stopOpacity="0.5" />
            <stop offset="100%" stopColor="white" stopOpacity="0" />
          </radialGradient>
          <mask id="cls-lattice-fade">
            <rect width="100%" height="100%" fill="url(#cls-lattice-mask)" />
          </mask>
        </defs>
        <rect width="100%" height="100%" fill="url(#cls-lattice)" mask="url(#cls-lattice-fade)" />
      </svg>
    </div>
  );
}
