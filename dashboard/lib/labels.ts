import type { StatusTone } from "./statusTone";

export type LabelEntry = {
  title: string;
  description?: string;
  icon?: string;
  tone?: StatusTone;
};

/**
 * Human labels for internal identifiers. Components call `labelFor`.
 * Raw ids stay in developer views only.
 */
const REGISTRY: Record<string, LabelEntry> = {
  "aggregate.destructive": {
    title: "Destructive burst",
    description: "Several destructive actions landed inside one window.",
    icon: "octagon-alert",
    tone: "danger",
  },
  "sequence.cls_impairment": {
    title: "CLS impairment",
    description: "A sequence that reduces what CLS can do in the server.",
    icon: "shield-alert",
    tone: "warning",
  },
  DEVELOPMENT_PROPOSAL: {
    title: "Provisional threshold",
    description: "This threshold is not production validated.",
    icon: "file-text",
    tone: "warning",
  },
  "channel.delete": { title: "Channel deletion", description: "Channels removed inside the time window.", tone: "danger" },
  "role.delete": { title: "Role deletion", description: "Roles removed inside the time window.", tone: "danger" },
  "member.ban_or_kick": { title: "Moderation burst", description: "Bans or kicks landed inside one window.", tone: "danger" },
  phishing: { title: "Phishing message", description: "A message matched the phishing patterns CLS watches.", tone: "danger" },
  human_honeypot: { title: "Human honeypot", description: "Someone posted in the visible honeypot channel.", tone: "warning" },
  bot_trap: { title: "Bot trap", description: "An untrusted bot posted in the bot trap channel.", tone: "warning" },
};

export function labelFor(id: string): LabelEntry {
  return (
    REGISTRY[id] ?? {
      title: "Unlisted identifier",
      description: "This identifier has no human label yet.",
      tone: "neutral",
    }
  );
}

export function registeredIds(): string[] {
  return Object.keys(REGISTRY);
}
