import { getServerSession } from "next-auth";
import { redirect } from "next/navigation";
import { authOptions } from "@/lib/auth";
import { isRootOwner } from "@/lib/utils";
import { AccessManagement } from "@/components/dashboard/access-management";

export default async function AccessPage() {
  const session = await getServerSession(authOptions);
  if (!session?.user?.id || !isRootOwner(session.user.id)) {
    redirect("/dashboard");
  }
  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-white">Dashboard Access</h1>
      <p className="text-slate-400">Root-only grant and role management.</p>
      <AccessManagement />
    </div>
  );
}
