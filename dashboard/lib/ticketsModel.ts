export type TicketRow = {
  id: string;
  number: number;
  status: string;
  opener_name?: string;
  opener_avatar?: string;
  assignee_name?: string;
  category_id?: string;
  category_name?: string;
  close_reason?: string;
  opened_at?: string | null;
  closed_at?: string | null;
  last_activity_at?: string | null;
};

export type TicketFilters = {
  status: string;
  categoryId: string;
  assignee: string;
  query: string;
};

export function ticketStatusLabel(status: string): string {
  if (status === "claimed") return "Claimed";
  if (status === "open") return "Open";
  if (status === "closed") return "Closed";
  if (status === "deleted") return "Deleted";
  if (status === "error") return "Needs attention";
  return "Open";
}

export function questionKindLabel(kind: string): string {
  return kind === "paragraph" ? "Paragraph" : "Short";
}

export function ageLabel(iso: string | null | undefined, now = Date.now()): string {
  if (!iso) return "—";
  const delta = Math.max(0, now - new Date(iso).getTime());
  const minutes = Math.floor(delta / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m`;
  const hours = Math.floor(minutes / 60);
  if (hours < 48) return `${hours}h`;
  return `${Math.floor(hours / 24)}d`;
}

export function filterTickets(rows: TicketRow[], filters: TicketFilters): TicketRow[] {
  const query = filters.query.trim().toLowerCase();
  return rows.filter((row) => {
    if (filters.status && filters.status !== "all" && row.status !== filters.status) return false;
    if (filters.categoryId && filters.categoryId !== "all" && row.category_id !== filters.categoryId) return false;
    if (filters.assignee === "unassigned" && (row.assignee_name || "").trim()) return false;
    if (filters.assignee && filters.assignee !== "all" && filters.assignee !== "unassigned" && (row.assignee_name || "") !== filters.assignee) return false;
    if (!query) return true;
    const haystack = [row.number, row.opener_name, row.close_reason, row.category_name, row.assignee_name].join(" ").toLowerCase();
    return haystack.includes(query);
  });
}

export function eventLabel(event: { kind?: string; actor_name?: string; payload?: Record<string, unknown> }): string {
  const actor = event.actor_name || "Staff";
  const payload = event.payload || {};
  const reason = typeof payload.reason === "string" ? payload.reason : "";
  const from = typeof payload.from === "string" ? payload.from : "";
  const to = typeof payload.to === "string" ? payload.to : "";
  switch (event.kind) {
    case "opened":
      return "Opened";
    case "claimed":
      return `Claimed by ${actor}`;
    case "unclaimed":
      return `Unclaimed by ${actor}`;
    case "member_added":
      return "Member added";
    case "member_removed":
      return "Member removed";
    case "transferred":
      return from || to ? `Transferred ${from || "team"} → ${to || "team"}` : "Transferred";
    case "closed":
      return reason ? `Closed: ${reason}` : "Closed";
    case "reopened":
      return "Reopened";
    case "transcript_generated":
      return "Transcript saved";
    case "deleted":
      return "Channel deleted";
    case "auto_close_warning":
      return "Inactivity warning";
    case "auto_closed":
      return "Closed automatically";
    case "channel_failed":
      return "Channel setup failed";
    default:
      return "Updated";
  }
}
