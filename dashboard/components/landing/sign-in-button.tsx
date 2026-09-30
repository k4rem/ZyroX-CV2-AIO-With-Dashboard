"use client";

import * as React from "react";
import { signIn } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { DiscordIcon } from "@/components/landing/discord-icon";
import { cn } from "@/lib/utils";

export interface SignInButtonProps {
  onLock?: () => void;
  className?: string;
  /** Hero primary vs restrained nav action */
  emphasis?: "primary" | "nav";
}

export function SignInButton({ onLock, className, emphasis = "primary" }: SignInButtonProps) {
  const [loading, setLoading] = React.useState(false);

  const handleClick = () => {
    if (loading) return;
    setLoading(true);
    onLock?.();
    void signIn("discord", { callbackUrl: "/auth/continue" });
  };

  if (emphasis === "nav") {
    return (
      <Button
        type="button"
        variant="ghost"
        size="md"
        className={cn("text-fg-2", className)}
        loading={loading}
        onClick={handleClick}
        aria-label="Sign in with Discord"
      >
        {!loading ? <DiscordIcon className="size-4 opacity-80" /> : null}
        {loading ? "Connecting…" : "Sign in"}
      </Button>
    );
  }

  return (
    <Button
      type="button"
      variant="primary"
      size="lg"
      className={className}
      loading={loading}
      onClick={handleClick}
      aria-label="Sign in with Discord"
    >
      {!loading ? <DiscordIcon className="size-5" /> : null}
      {loading ? "Connecting to Discord…" : "Sign in with Discord"}
    </Button>
  );
}
