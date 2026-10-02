import { notFound } from "next/navigation";
import { MenuBuilder } from "@/components/dashboard/role-menus/menu-builder";
import { api } from "@/lib/api";

export default async function EditRoleMenuPage({ params }: { params: { guildId: string; menuId: string } }) {
  const [menu, roles, channels, emojis] = await Promise.all([
    api.getRoleMenu(params.guildId, params.menuId).catch(() => null),
    api.getRoles(params.guildId).catch(() => []),
    api.getChannels(params.guildId).catch(() => []),
    api.listGuildEmojis(params.guildId).catch(() => ({ emojis: [] })),
  ]);
  if (!menu) notFound();
  const roleOptions = (roles || []).filter((role: { name: string }) => role.name !== "@everyone").map((role: { id: string | number; name: string; color?: number; position?: number }) => ({ id: String(role.id), name: role.name, color: role.color, position: role.position }));
  const textChannels = (channels || []).filter((channel: { type?: string }) => ["0", "5", "text", "news"].includes(String(channel.type))).map((channel: { id: string | number; name: string; type?: string; parent_id?: string | null }) => ({ id: String(channel.id), name: channel.name, type: String(channel.type ?? "0"), parent_id: channel.parent_id ? String(channel.parent_id) : null }));
  const botPosition = menu.bot_position || 0;
  return <MenuBuilder guildId={params.guildId} menu={menu} roles={roleOptions} channels={textChannels} emojis={emojis?.emojis ?? []} botPosition={botPosition} />;
}
