export type GiveawayRow = {
  id: string;
  prize: string;
  description: string;
  channel_id: string | null;
  status: string;
  ends_at: string;
  starts_at: string | null;
  winner_count: number;
  winner_ids: string[];
  winners: { id: string; name: string }[];
  required_role_id: string | null;
  blocked_role_id: string | null;
  host_id: string | null;
  host_name: string | null;
  entry_count: number;
};

export type GiveawayView = "scheduled" | "live" | "ended";

export function giveawayView(status: string): GiveawayView {
  if (status === "scheduled") return "scheduled";
  if (status === "open") return "live";
  return "ended";
}

export function filterGiveaways(rows: GiveawayRow[], view: GiveawayView) {
  return rows.filter((row) => giveawayView(row.status) === view);
}

export function giveawayPreview(input: { prize: string; description: string; winnerCount: number; endsAt: string; host: string }) {
  const ends = input.endsAt ? new Date(input.endsAt) : null;
  const when = ends && !Number.isNaN(ends.getTime()) ? ends.toLocaleString(undefined, { month: "short", day: "numeric", hour: "numeric", minute: "2-digit" }) : "the end time";
  const lines = [input.prize || "Prize"];
  if (input.description.trim()) lines.push(input.description.trim());
  lines.push(`Winners: ${input.winnerCount}`);
  lines.push(`Ends ${when}`);
  lines.push(`Host: ${input.host || "you"}`);
  lines.push("Entries: 0");
  return lines.join("\n");
}
