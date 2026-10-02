import { redirect } from "next/navigation";

export default function JoinDmPage({ params }: { params: { guildId: string } }) {
  redirect(`/dashboard/guild/${params.guildId}/welcome?tab=dm`);
}
