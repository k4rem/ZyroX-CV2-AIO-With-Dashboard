"use client";

import Link from "next/link";
import { signIn } from "next-auth/react";
import { AuthLayout } from "@/components/auth/auth-layout";
import { Button } from "@/components/ui/button";

function errorCopy(code: string | null): { title: string; body: string; reference?: string } {
  switch (code) {
    case "AccessDenied":
      return {
        title: "Sign-in was cancelled on Discord.",
        body: "You can try again when you are ready to continue into CLS OS.",
        reference: code ? `Reference: ${code}` : undefined,
      };
    case "Configuration":
      return {
        title: "Sign-in isn't configured correctly on this server.",
        body: "Tell the CLS root owner. OAuth client settings must be valid for this dashboard URL.",
        reference: code ? `Reference: ${code}` : undefined,
      };
    case "ServiceUnavailable":
      return {
        title: "CLS OS can't reach the bot service right now.",
        body: "Try again in a minute. If this keeps happening, contact the CLS root owner.",
        reference: code ? `Reference: ${code}` : undefined,
      };
    case "OAuthCallback":
    case "Callback":
    case "OAuthSignin":
    default:
      return {
        title: "Discord sign-in didn't complete.",
        body: "Something interrupted the OAuth flow. Try signing in again.",
        reference: code ? `Reference: ${code}` : undefined,
      };
  }
}

export function AuthErrorClient({ code }: { code: string | null }) {
  const copy = errorCopy(code);

  return (
    <AuthLayout
      title={copy.title}
      actions={
        <>
          <Button
            type="button"
            variant="primary"
            size="lg"
            onClick={() => signIn("discord", { callbackUrl: "/auth/continue" })}
          >
            Try again
          </Button>
          <Button variant="secondary" size="lg" asChild>
            <Link href="/">Back to CLS OS</Link>
          </Button>
        </>
      }
    >
      <p>{copy.body}</p>
      {copy.reference ? <p className="mt-4 font-mono text-caption text-fg-3">{copy.reference}</p> : null}
    </AuthLayout>
  );
}
