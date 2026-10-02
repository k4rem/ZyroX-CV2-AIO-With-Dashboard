"use client";

import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/button";
import { ErrorState } from "@/components/ui/state";
import { loadFailure } from "@/lib/loadFailure";

export function LoadError({
  title,
  error,
}: {
  title: string;
  error?: unknown;
}) {
  const router = useRouter();
  const failure = loadFailure(error, title);
  return (
    <ErrorState
      title={failure.title}
      description={failure.message}
      reference={failure.reference ?? undefined}
      actions={
        <Button type="button" onClick={() => router.refresh()}>
          Retry
        </Button>
      }
    />
  );
}
