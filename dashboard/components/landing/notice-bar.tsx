import { InlineBanner } from "@/components/ui/state";

export type GatewayNotice = "session-ended" | "signed-out";

const COPY: Record<GatewayNotice, { title: string; body: string }> = {
  "session-ended": {
    title: "Your session ended.",
    body: "Sign in again to continue.",
  },
  "signed-out": {
    title: "Signed out.",
    body: "You can sign in again when you are ready.",
  },
};

export function NoticeBar({ notice }: { notice?: string | null }) {
  if (notice !== "session-ended" && notice !== "signed-out") return null;
  const copy = COPY[notice];
  return (
    <div className="mx-auto w-full max-w-6xl px-4 pt-3 md:px-6">
      <InlineBanner tone="info" title={copy.title}>
        {copy.body}
      </InlineBanner>
    </div>
  );
}
