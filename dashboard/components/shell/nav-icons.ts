import {
  AudioLines,
  Cpu,
  DoorOpen,
  KeyRound,
  LayoutDashboard,
  MessagesSquare,
  Link2,
  ScrollText,
  Server,
  ShieldAlert,
  ShieldCheck,
  SlidersHorizontal,
  SmilePlus,
  Tags,
  ThumbsUp,
  Ticket,
  UserPlus,
  type LucideIcon,
} from "lucide-react";
import type { NavIconKey } from "@/lib/shellNav";

/**
 * Icon per navigation item. lucide-react only (DS §11). Icons identify an item;
 * they carry no meaning on their own, every item also renders a text label.
 * `verification` and `leveling` are reserved keys: those modules are not surfaced
 * in Phase 1.5 navigation, so they intentionally have no glyph here.
 */
export const NAV_ICONS: Partial<Record<NavIconKey, LucideIcon>> = {
  overview: LayoutDashboard,
  servers: Server,
  roles: Tags,
  tickets: Ticket,
  welcome: DoorOpen,
  autorole: UserPlus,
  reactionroles: SmilePlus,
  autoreact: ThumbsUp,
  invites: Link2,
  j2c: AudioLines,
  automod: ShieldCheck,
  logging: ScrollText,
  messages: MessagesSquare,
  antinuke: ShieldAlert,
  settings: SlidersHorizontal,
  access: KeyRound,
  platform: Cpu,
};

export function iconForNav(key: NavIconKey): LucideIcon {
  return NAV_ICONS[key] ?? LayoutDashboard;
}
