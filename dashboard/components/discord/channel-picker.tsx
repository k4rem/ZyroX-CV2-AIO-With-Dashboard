"use client";

import { Select } from "@/components/ui/select";
import { InlineHealth } from "@/components/platform/health";
import {
  channelChecks,
  roleChecks,
  type ChannelCapabilities,
  type ChannelCapability,
} from "@/lib/platformHealth";

export type ChannelOption = {
  id: string;
  name: string;
  type: string;
  parent_id?: string | null;
  parent_name?: string | null;
};

const TEXT = new Set(["0", "5", "text", "news", "guild_text", "guild_news"]);

export function textChannels(channels: ChannelOption[]): ChannelOption[] {
  return channels.filter((channel) => TEXT.has(String(channel.type)));
}

export function ChannelPicker({
  channels,
  value,
  onChange,
  capabilities,
  required = [],
  intent = "display",
}: {
  channels: ChannelOption[];
  value: string;
  onChange: (id: string) => void;
  capabilities?: Record<string, ChannelCapabilities>;
  required?: ChannelCapability[];
  intent?: "display" | "mutate";
}) {
  const options = textChannels(channels).map((channel) => ({
    value: channel.id,
    label: channel.parent_name ? `${channel.parent_name} / #${channel.name}` : `#${channel.name}`,
  }));
  const caps = value && capabilities ? capabilities[value] : undefined;
  const checks = intent === "mutate" && caps && required.length ? channelChecks(caps, required) : [];
  return (
    <div>
      <Select value={value} onValueChange={onChange} options={options} placeholder="Choose a channel" />
      <InlineHealth checks={checks} />
    </div>
  );
}

export type RoleOption = {
  id: string;
  name: string;
  position?: number;
  managed?: boolean;
};

export function RolePicker({
  roles,
  value,
  onChange,
  botPosition,
  botRoleId,
  manageRoles,
  intent = "display",
  allowEmpty = false,
}: {
  roles: RoleOption[];
  value: string;
  onChange: (id: string) => void;
  botPosition?: number | null;
  botRoleId?: string | null;
  manageRoles?: boolean | null;
  intent?: "display" | "mutate";
  allowEmpty?: boolean;
}) {
  const selected = roles.find((role) => role.id === value);
  const checks =
    intent === "mutate" && selected
      ? roleChecks({
          managed: Boolean(selected.managed),
          position: selected.position,
          roleId: selected.id,
          botPosition,
          botRoleId,
          manageRoles,
        })
      : [];
  return (
    <div>
      <Select
        value={value}
        onValueChange={onChange}
        options={[
          ...(allowEmpty ? [{ value: "", label: "No role" }] : []),
          ...roles.filter((role) => role.name !== "@everyone").map((role) => ({ value: role.id, label: role.name })),
        ]}
        placeholder="Choose a role"
      />
      <InlineHealth checks={checks} />
    </div>
  );
}
