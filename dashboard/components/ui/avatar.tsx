import * as React from "react";
import Image from "next/image";
import { cn } from "@/lib/utils";

/**
 * Avatar / guild icon. Discord convention is round (DS §8 `radius-full`); this is the
 * only place icons sit inside a rounded container.
 */
export function Avatar({
  src,
  name,
  size = 28,
  className,
}: {
  src?: string | null;
  name?: string | null;
  size?: number;
  className?: string;
}) {
  const initial = (name ?? "?").trim().charAt(0).toUpperCase() || "?";
  return (
    <span
      className={cn(
        "inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-surface-4 font-medium text-fg-2",
        className,
      )}
      style={{ width: size, height: size, fontSize: Math.max(10, Math.round(size * 0.42)) }}
    >
      {src ? (
        <Image src={src} alt="" width={size} height={size} unoptimized className="size-full object-cover" />
      ) : (
        <span aria-hidden="true" dir="auto">
          {initial}
        </span>
      )}
    </span>
  );
}

export const GuildIcon = Avatar;
