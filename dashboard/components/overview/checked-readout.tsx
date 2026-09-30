"use client";

import * as React from "react";
import { useRouter } from "next/navigation";
import { RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

/** "Checked hh:mm:ss" plus a re-check. The time is formatted in the viewer's zone after mount. */
export function CheckedReadout({ checkedAt }: { checkedAt: string }) {
  const router = useRouter();
  const [pending, startTransition] = React.useTransition();
  const [text, setText] = React.useState<string | null>(null);

  React.useEffect(() => {
    setText(
      new Date(checkedAt).toLocaleTimeString(undefined, {
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
        hour12: false,
      }),
    );
  }, [checkedAt]);

  return (
    <span className="flex min-w-0 items-center gap-2">
      <time dateTime={checkedAt} dir="ltr" className="font-mono tabular-nums" aria-live="polite">
        {pending ? "Checking…" : text ?? "\u00a0"}
      </time>
      <button
        type="button"
        onClick={() => startTransition(() => router.refresh())}
        disabled={pending}
        aria-label="Check again"
        title="Check again"
        className={cn(
          "-my-2.5 inline-flex size-10 shrink-0 items-center justify-center rounded-sm text-fg-3 md:-my-1 md:size-7",
          "transition-colors duration-micro ease-cls-out hover:bg-surface-3 hover:text-fg-1 disabled:text-fg-4",
        )}
      >
        <RefreshCw className="size-3.5" strokeWidth={1.75} aria-hidden="true" />
      </button>
    </span>
  );
}
