"use client";

import { signOut } from "next-auth/react";
import { Button } from "@/components/ui/button";

export function SignOutButton() {
  return (
    <Button
      type="button"
      variant="secondary"
      size="lg"
      onClick={() => void signOut({ callbackUrl: "/?notice=signed-out" })}
    >
      Sign out
    </Button>
  );
}
