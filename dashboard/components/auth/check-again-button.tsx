"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";

export function CheckAgainButton() {
  const router = useRouter();
  const [pending, setPending] = React.useState(false);

  return (
    <Button
      type="button"
      variant="primary"
      size="lg"
      loading={pending}
      onClick={() => {
        setPending(true);
        router.push("/auth/continue");
      }}
    >
      {pending ? "Checking…" : "Check again"}
    </Button>
  );
}
