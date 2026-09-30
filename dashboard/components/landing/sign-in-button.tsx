"use client";

import * as React from "react";
import { signIn } from "next-auth/react";
import { Button } from "@/components/ui/button";
import { DiscordIcon } from "@/components/landing/discord-icon";

export interface SignInButtonProps {
  onLock?: () => void;
  className?: string;
}

export function SignInButton({ onLock, className }: SignInButtonProps) {
  const [loading, setLoading] = React.useState(false);

  const handleClick = () => {
    if (loading) return;
    setLoading(true);
    onLock?.();
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const delay = reduced ? 0 : 480;
    window.setTimeout(() => {
      void signIn("discord", { callbackUrl: "/auth/continue" });
    }, delay);
  };

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
