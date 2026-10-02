import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { AuthLayout } from "@/components/auth/auth-layout";
import { InlineBanner } from "@/components/ui/state";
import { CheckAgainButton } from "@/components/auth/check-again-button";
import { CopyIdButton } from "@/components/auth/copy-id-button";
import { SignOutButton } from "@/components/auth/sign-out-button";

export const dynamic = "force-dynamic";

export default async function NoAccessPage() {
  const session = await getServerSession(authOptions);
  const userId = session?.user?.id;
  if (!session || !userId) {
    redirect("/");
  }

  const name = session.user?.name ?? "Discord user";
  const image = session.user?.image;

  return (
    <AuthLayout title="Awaiting access" ambient actions={<><CheckAgainButton /><SignOutButton /></>}>
      <InlineBanner tone="ok" title="Signed in">
        <span className="mt-1 flex items-center gap-2">
          {image ? (
            // Discord avatars are already hosted; keep native drag disabled.
            // eslint-disable-next-line @next/next/no-img-element
            <img src={image} alt="" width={32} height={32} draggable={false} className="size-8 rounded-full" />
          ) : (
            <span className="flex size-8 items-center justify-center rounded-full bg-surface-3 text-caption text-fg-2" aria-hidden="true">
              {name.slice(0, 1).toUpperCase()}
            </span>
          )}
          <span className="text-fg-1">{name}</span>
        </span>
      </InlineBanner>
      <div className="mt-3 text-start">
        <InlineBanner tone="locked" title="Awaiting access grant">
          The CLS owner has not granted this account yet.
        </InlineBanner>
      </div>
      <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
        <span className="cls-mono-data text-fg-2" dir="ltr">
          {userId}
        </span>
        <CopyIdButton value={userId} />
      </div>
      <p className="mt-4 text-small text-fg-3">
        What happens next: share your Discord ID with the CLS owner, then check again. Discord Administrator does not grant access by itself.
      </p>
    </AuthLayout>
  );
}
