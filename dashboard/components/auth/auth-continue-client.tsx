"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { AuthLayout } from "@/components/auth/auth-layout";

export function AuthContinueClient({ destination }: { destination: string }) {
  const router = useRouter();
  const [open, setOpen] = React.useState(false);

  React.useEffect(() => {
    router.replace(destination);
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    if (!reduced) setOpen(true);
  }, [destination, router]);

  return (
    <AuthLayout title="Access confirmed" perimeterOpen={open}>
      <p className="text-center">Opening CLS OS…</p>
    </AuthLayout>
  );
}
