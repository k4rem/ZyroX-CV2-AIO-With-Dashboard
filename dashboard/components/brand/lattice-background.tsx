import * as React from "react";
import { cn } from "@/lib/utils";

/**
 * Faint isometric lattice (DS §9.5, §13). Decorative only; masked so it never competes with content.
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
      <svg className="absolute inset-0 h-full w-full text-fg-3/20" preserveAspectRatio="xMidYMid slice">
        <defs>
          <pattern id="cls-lattice" width="28" height="48" patternUnits="userSpaceOnUse" patternTransform="scale(1.2)">
            <path
              d="M0 24 L14 0 L28 0 L14 24 L28 48 L14 48 L0 24 Z"
              fill="none"
              stroke="currentColor"
              strokeWidth="0.5"
            />
          </pattern>
          <radialGradient id="cls-lattice-mask" cx="50%" cy="45%" r="65%">
            <stop offset="0%" stopColor="white" stopOpacity="0.55" />
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
