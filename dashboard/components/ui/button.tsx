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

"use client";

import * as React from "react";
import { Slot } from "@radix-ui/react-slot";
import { cva, type VariantProps } from "class-variance-authority";
import { cn } from "@/lib/utils";
import { HexLoader } from "@/components/brand/hex-loader";

/**
 * Button system (DS §21): five variants plus danger-secondary. Purple fill is
 * reserved for `primary` (one per region). `default`, `destructive`, `outline`
 * and `link` are legacy aliases kept so pre-CLS pages compile until Task C.
 */
const buttonVariants = cva(
  [
    "inline-flex select-none items-center justify-center gap-1.5 whitespace-nowrap rounded-sm text-body font-medium",
    "transition-[background-color,border-color,color,box-shadow,transform] duration-micro ease-cls-out",
    "active:scale-[0.98] active:duration-instant",
    "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-300",
    "disabled:cursor-not-allowed disabled:border-transparent disabled:bg-surface-2 disabled:text-fg-4 disabled:opacity-60 disabled:shadow-none disabled:active:scale-100",
    "aria-busy:cursor-progress aria-disabled:active:scale-100",
    "[&_svg]:shrink-0",
  ],
  {
    variants: {
      variant: {
        primary:
          "bg-brand-600 text-white hover:bg-brand-500 hover:shadow-glow-g1 active:bg-brand-700 disabled:hover:shadow-none",
        secondary:
          "border border-line-strong bg-surface-3 text-fg-1 hover:bg-surface-4 active:bg-surface-4",
        ghost: "text-fg-2 hover:bg-surface-3 hover:text-fg-1 active:bg-surface-4",
        tertiary:
          "h-auto rounded-xs px-0 text-brand-400 hover:underline active:text-brand-300 disabled:bg-transparent",
        danger:
          "bg-danger-fill text-white hover:bg-danger-fill-hover active:bg-danger-fill-active",
        "danger-secondary":
          "border border-danger/30 text-danger hover:bg-danger/10 active:bg-danger/20",
        // Legacy aliases
        default:
          "bg-brand-600 text-white hover:bg-brand-500 hover:shadow-glow-g1 active:bg-brand-700 disabled:hover:shadow-none",
        destructive:
          "bg-danger-fill text-white hover:bg-danger-fill-hover active:bg-danger-fill-active",
        outline:
          "border border-line-strong bg-surface-3 text-fg-1 hover:bg-surface-4 active:bg-surface-4",
        link: "h-auto rounded-xs px-0 text-brand-400 hover:underline active:text-brand-300 disabled:bg-transparent",
      },
      size: {
        sm: "h-7 px-2.5",
        md: "h-8 px-3",
        lg: "h-10 px-4",
        default: "h-8 px-3",
        icon: "h-8 w-8 p-0",
        "icon-sm": "h-7 w-7 p-0",
        "icon-lg": "h-10 w-10 p-0",
      },
    },
    compoundVariants: [
      // The inline link variant must not pick up a fixed control height from `size`.
      { variant: "link", className: "h-auto px-0" },
    ],
    defaultVariants: {
      variant: "primary",
      size: "md",
    },
  },
);

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
  asChild?: boolean;
  /** Shows the hex loader, sets aria-busy and ignores clicks. Not supported with asChild. */
  loading?: boolean;
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className, variant, size, asChild = false, loading = false, children, onClick, disabled, ...props }, ref) => {
    const classes = cn(buttonVariants({ variant, size }), className);

    if (asChild) {
      return (
        <Slot className={classes} ref={ref} {...props}>
          {children}
        </Slot>
      );
    }

    return (
      <button
        ref={ref}
        className={classes}
        disabled={disabled}
        aria-busy={loading || undefined}
        aria-disabled={loading || undefined}
        onClick={loading ? (e) => e.preventDefault() : onClick}
        {...props}
      >
        {loading ? <HexLoader size={14} className="text-current" /> : null}
        {children}
      </button>
    );
  },
);
Button.displayName = "Button";

export { Button, buttonVariants };
