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

import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

/**
 * Text input (DS §20.2): 32 px, surface-well, 1 px line-input, radius-sm.
 * Focus switches the border to brand-400 and adds the ring with zero offset.
 */
const Input = React.forwardRef<HTMLInputElement, InputProps>(({ className, type, ...props }, ref) => {
  return (
    <input
      type={type}
      className={cn(
        "flex h-8 w-full rounded-sm border border-line-input bg-surface-well px-2.5 text-body text-fg-1 shadow-well",
        "placeholder:text-fg-3 file:border-0 file:bg-transparent file:text-body file:font-medium",
        "transition-colors duration-micro hover:border-fg-3",
        "focus-visible:border-brand-400 focus-visible:outline-brand-400 focus-visible:outline-offset-0",
        "disabled:cursor-not-allowed disabled:border-line-subtle disabled:text-fg-4 disabled:hover:border-line-subtle",
        "aria-[invalid=true]:border-danger/60",
        className,
      )}
      ref={ref}
      {...props}
    />
  );
});
Input.displayName = "Input";

export { Input };
