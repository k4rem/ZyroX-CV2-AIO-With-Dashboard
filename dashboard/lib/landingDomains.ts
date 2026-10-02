/** Real CLS OS domains shown on the public entrance. No future modules. */
export const PERIMETER_DOMAINS = [
  "Security",
  "Tickets",
  "Logging",
  "Messaging",
  "Roles",
  "Automation",
] as const;

export type PerimeterDomain = (typeof PERIMETER_DOMAINS)[number];

export interface LandingDomain {
  id: PerimeterDomain;
  name: string;
  hint: string;
  summary: string;
  capabilities: readonly string[];
  surface: readonly string[];
  previewTitle: string;
  previewRows: readonly string[];
}

export const LANDING_DOMAINS: readonly LandingDomain[] = [
  {
    id: "Security",
    name: "Security",
    hint: "Incidents and trust",
    summary: "Observe threats, investigate incidents, and safely move toward enforcement.",
    capabilities: ["Incidents", "Detectors", "Trust", "Quarantine"],
    surface: ["Incidents", "Detectors", "Trust", "Quarantine"],
    previewTitle: "Incident",
    previewRows: ["Mass channel deletion — Open", "Detector: channel delete", "Posture: Observe"],
  },
  {
    id: "Tickets",
    name: "Tickets",
    hint: "Queue and panels",
    summary: "Staff work the live queue. Members still open tickets in Discord.",
    capabilities: ["Live queue", "Panels", "Transcripts"],
    surface: ["Live queue", "Panels", "Transcripts"],
    previewTitle: "Queue",
    previewRows: ["#support — Waiting on staff", "Panel: General", "Transcript kept after close"],
  },
  {
    id: "Logging",
    name: "Logging",
    hint: "Event record",
    summary: "A record of what changed, who did it, and where the log was sent.",
    capabilities: ["Event history", "Routing", "Attribution"],
    surface: ["Event history", "Routing", "Attribution"],
    previewTitle: "Event",
    previewRows: ["Role added — certain", "Message edited", "Route: stored only"],
  },
  {
    id: "Messaging",
    name: "Messaging",
    hint: "Welcome and templates",
    summary: "Welcome, goodbye, and the messages you save to send again.",
    capabilities: ["Welcome", "Welcome DM", "Saved templates"],
    surface: ["Welcome", "Welcome DM", "Saved templates"],
    previewTitle: "Message",
    previewRows: ["Welcome — ready to publish", "Channel chosen in the composer", "Template saved for reuse"],
  },
  {
    id: "Roles",
    name: "Roles",
    hint: "Menus and rules",
    summary: "Menus and rules that give roles when a member qualifies.",
    capabilities: ["Role menus", "Join roles", "Automation rules"],
    surface: ["Role menus", "Join roles", "Automation rules"],
    previewTitle: "Roles",
    previewRows: ["Menu: reaction, button, or select", "Join role on entry", "Rule waits for a condition"],
  },
  {
    id: "Automation",
    name: "Automation",
    hint: "Automod, voice, commands",
    summary: "Automod, voice rooms, reactions, and which commands are available.",
    capabilities: ["Automod", "Join to Create", "Commands"],
    surface: ["Automod", "Join to Create", "Commands"],
    previewTitle: "Commands",
    previewRows: ["Moderation module — enabled", "Flood rule in Automod", "Join to Create room"],
  },
];

export const DISCORD_ENTRY = {
  provider: "discord",
  callbackUrl: "/auth/continue",
  label: "Sign in with Discord",
} as const;

export function neighborDomain(id: PerimeterDomain, delta: number): PerimeterDomain {
  const index = PERIMETER_DOMAINS.indexOf(id);
  const next = (index + delta + PERIMETER_DOMAINS.length) % PERIMETER_DOMAINS.length;
  return PERIMETER_DOMAINS[next];
}

export function landingDomain(id: PerimeterDomain): LandingDomain {
  const found = LANDING_DOMAINS.find((domain) => domain.id === id);
  if (!found) return LANDING_DOMAINS[0];
  return found;
}
