import { MenusView } from "@/components/dashboard/role-menus/menus-view";
import { api } from "@/lib/api";

export default async function RoleMenusPage({ params }: { params: { guildId: string } }) {
  const [menus, channels] = await Promise.all([
    api.getRoleMenus(params.guildId).catch(() => ({ menus: [] })),
    api.getChannels(params.guildId).catch(() => []),
  ]);
  const channelNames = Object.fromEntries((channels || []).map((channel: { id: string | number; name: string }) => [String(channel.id), channel.name]));
  return <MenusView guildId={params.guildId} menus={menus.menus || []} channelNames={channelNames} />;
}
