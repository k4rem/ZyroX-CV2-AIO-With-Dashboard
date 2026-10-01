"use client";

import { Select } from "@/components/ui/select";

export type ChannelOption = { id: string; name: string; type: string; parent_id?: string | null; parent_name?: string | null };

const TEXT = new Set(["0", "5", "text", "news", "guild_text", "guild_news"]);

export function textChannels(channels: ChannelOption[]): ChannelOption[] {
  return channels.filter((channel) => TEXT.has(String(channel.type)));
}

export function ChannelPicker({
  channels,
  value,
  onChange,
}: {
  channels: ChannelOption[];
  value: string;
  onChange: (id: string) => void;
}) {
  const options = textChannels(channels).map((channel) => ({
    value: channel.id,
    label: channel.parent_name ? `${channel.parent_name} / #${channel.name}` : `#${channel.name}`,
  }));
  return <Select value={value} onValueChange={onChange} options={options} placeholder="Choose a channel" />;
}

export function RolePicker({
  roles,
  value,
  onChange,
}: {
  roles: Array<{ id: string; name: string }>;
  value: string;
  onChange: (id: string) => void;
}) {
  return (
    <Select
      value={value}
      onValueChange={onChange}
      options={roles.filter((role) => role.name !== "@everyone").map((role) => ({ value: role.id, label: role.name }))}
      placeholder="Choose a role"
    />
  );
}
