"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { HexLoader } from "@/components/brand/hex-loader";
import { AuthLayout } from "@/components/auth/auth-layout";
import { Avatar } from "@/components/ui/avatar";

export function AuthContinueClient({
  destination,
  userName,
  userImage,
}: {
  destination: string;
  userName: string | null;
  userImage: string | null;
}) {
  const router = useRouter();
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const animMs = reduced ? 0 : 420;
    const t1 = window.setTimeout(() => setOpen(true), animMs * 0.4);
    const t2 = window.setTimeout(() => router.replace(destination), Math.max(animMs, 320));
    return () => {
      window.clearTimeout(t1);
      window.clearTimeout(t2);
    };
  }, [destination, router]);

  return (
    <AuthLayout title="Checking your access" perimeterOpen={open}>
      <div className="flex flex-col items-center gap-4 text-center">
        <Avatar src={userImage ?? undefined} name={userName ?? "User"} size={48} />
        {userName ? <p className="text-body text-fg-1">{userName}</p> : null}
        <div className="flex items-center justify-center gap-2 text-fg-2">
          <HexLoader size={16} />
          <span>Confirming CLS OS access…</span>
        </div>
      </div>
    </AuthLayout>
  );
}
