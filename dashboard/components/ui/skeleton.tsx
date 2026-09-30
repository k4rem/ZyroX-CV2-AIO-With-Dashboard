import * as React from "react";
import { cn } from "@/lib/utils";

/** Loading block (DS §25): surface-3 with one shimmer sweep. Static under reduced motion. */
export function Skeleton({ className, ...props }: React.HTMLAttributes<HTMLDivElement>) {
  return <div aria-hidden="true" className={cn("cls-shimmer rounded-sm", className)} {...props} />;
}
