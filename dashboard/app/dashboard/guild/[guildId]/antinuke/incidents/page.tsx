import { SecurityPage } from "@/components/dashboard/security-page";

export default function Page({ params }: { params: { guildId: string } }) {
  return <SecurityPage guildId={params.guildId} tab="incidents" />;
}
