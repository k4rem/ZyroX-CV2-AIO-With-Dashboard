import { redirect } from "next/navigation";
import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { AuthLayout } from "@/components/auth/auth-layout";
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

  return (
    <AuthLayout
      title="No access yet"
      actions={
        <>
          <SignOutButton />
        </>
      }
    >
      <p className="text-center text-body-prose">
        You&apos;re signed in as <span className="text-fg-1">{name}</span>. Access to CLS OS is granted by the CLS
        owner. Discord Administrator permission does not grant dashboard access. Share your Discord ID below if you
        need access.
      </p>
      <div className="mt-4 flex flex-wrap items-center justify-center gap-2">
        <span className="cls-mono-data text-fg-2" dir="ltr">
          {userId}
        </span>
        <CopyIdButton value={userId} />
      </div>
    </AuthLayout>
  );
}
