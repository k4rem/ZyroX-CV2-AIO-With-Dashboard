"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { signOut } from "next-auth/react";
import { Check, Copy, Languages, LogOut } from "lucide-react";
import { cn } from "@/lib/utils";
import { Avatar } from "@/components/ui/avatar";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import type { ShellUser } from "./shell-types";

export const DIR_COOKIE = "cls_dir";

/**
 * Account menu (DS §15.5). Shows who the session belongs to and whether the server
 * granted root access (a server-computed prop, never derived in the browser).
 * The direction toggle exists in development builds only, to exercise RTL layout
 * before Arabic copy exists.
 */
export function UserMenu({
  user,
  isRoot,
  dir,
  showDevTools,
}: {
  user: ShellUser;
  isRoot: boolean;
  dir: "ltr" | "rtl";
  showDevTools: boolean;
}) {
  const router = useRouter();
  const [copied, setCopied] = React.useState(false);
  const displayName = user.name?.trim() || "Discord user";

  React.useEffect(() => {
    if (!copied) return;
    const t = setTimeout(() => setCopied(false), 1600);
    return () => clearTimeout(t);
  }, [copied]);

  const copyId = async (e: Event) => {
    e.preventDefault();
    try {
      await navigator.clipboard.writeText(user.id);
      setCopied(true);
    } catch {
      /* clipboard unavailable: nothing to do */
    }
  };

  const toggleDir = () => {
    const next = dir === "rtl" ? "ltr" : "rtl";
    document.cookie = `${DIR_COOKIE}=${next}; path=/; max-age=86400; samesite=lax`;
    router.refresh();
  };

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <button
          type="button"
          aria-label={`Account menu for ${displayName}`}
          className={cn(
            "flex size-10 items-center justify-center rounded-full outline-none md:size-8 transition-shadow duration-micro",
            "hover:ring-2 hover:ring-line-strong data-[state=open]:ring-2 data-[state=open]:ring-line-strong",
            "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-400",
          )}
        >
          <Avatar src={user.image} name={displayName} size={28} />
        </button>
      </DropdownMenuTrigger>

      <DropdownMenuContent align="end" className="w-[248px]">
        <DropdownMenuLabel className="flex items-center gap-2.5">
          <Avatar src={user.image} name={displayName} size={32} />
          <span className="min-w-0">
            <span className="block truncate text-body font-medium text-fg-1" dir="auto">
              {displayName}
            </span>
            <span className="block truncate text-small text-fg-3">
              {isRoot ? "Root owner" : "Authorized operator"}
            </span>
          </span>
        </DropdownMenuLabel>
        <DropdownMenuSeparator />

        <DropdownMenuItem onSelect={copyId}>
          {copied ? <Check className="text-ok" strokeWidth={1.5} /> : <Copy strokeWidth={1.5} />}
          <span className="flex-1">{copied ? "Copied" : "Copy Discord ID"}</span>
        </DropdownMenuItem>
        <p className="px-2 pb-1 ps-8 text-caption text-fg-3">
          <bdi dir="ltr" className="cls-mono-data">
            {user.id}
          </bdi>
        </p>

        {showDevTools ? (
          <DropdownMenuItem onSelect={toggleDir}>
            <Languages strokeWidth={1.5} />
            <span className="flex-1">Direction: {dir.toUpperCase()}</span>
            <span className="text-small text-fg-3">Dev</span>
          </DropdownMenuItem>
        ) : null}

        <DropdownMenuSeparator />
        <DropdownMenuItem onSelect={() => void signOut({ callbackUrl: "/" })}>
          <LogOut className="cls-mirror" strokeWidth={1.5} />
          Sign out
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
