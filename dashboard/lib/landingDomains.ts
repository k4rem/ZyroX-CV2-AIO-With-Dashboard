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
}

export const LANDING_DOMAINS: readonly LandingDomain[] = [
  {
    id: "Security",
    name: "Security",
    hint: "Antinuke",
    summary: "Antinuke watches destructive changes and records who made them.",
    capabilities: ["Human protection", "Bot protection", "Rules", "Trusted actors"],
    surface: ["Human protection", "Bot protection", "Rules", "Trusted actors"],
  },
  {
    id: "Tickets",
    name: "Tickets",
    hint: "Queue and panels",
    summary: "Categories, panels, and the live queue. Tickets still open in Discord.",
    capabilities: ["Live queue", "Panels", "Categories and teams", "Transcripts"],
    surface: ["Live queue", "Panels", "Categories", "Transcripts"],
  },
  {
    id: "Logging",
    name: "Logging",
    hint: "Event routes",
    summary: "Choose where each kind of event is written.",
    capabilities: ["Category routes", "Event routes", "Appearance", "Exclusions"],
    surface: ["Category routes", "Event routes", "Appearance", "Exclusions"],
  },
  {
    id: "Messaging",
    name: "Messaging",
    hint: "Welcome and templates",
    summary: "Welcome, goodbye, and the messages you save to send again.",
    capabilities: ["Welcome", "Welcome DM", "Goodbye", "Saved templates"],
    surface: ["Welcome", "Welcome DM", "Goodbye", "Templates"],
  },
  {
    id: "Roles",
    name: "Roles",
    hint: "Menus and rules",
    summary: "Menus, join roles, and rules that assign roles when conditions match.",
    capabilities: ["Role menus", "Join roles", "Role automation", "Delays"],
    surface: ["Role menus", "Join roles", "Rules", "Delays"],
  },
  {
    id: "Automation",
    name: "Automation",
    hint: "Voice, reactions, automod",
    summary: "Automod, voice channels, reactions, and which commands are available.",
    capabilities: ["Automod", "Join to Create", "Auto React", "Commands"],
    surface: ["Automod", "Join to Create", "Auto React", "Commands"],
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
