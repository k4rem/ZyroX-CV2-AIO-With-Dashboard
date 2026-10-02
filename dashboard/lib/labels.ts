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
    title: "Development proposal",
    description: "A change proposed from the development workflow.",
    icon: "file-text",
    tone: "info",
  },
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
