export type InviteMember = {
  user_id: string;
  name: string;
  valid: number;
  left: number;
  codes: string[];
};

export type InviteOverview = {
  members: InviteMember[];
  uncredited: { ambiguous: number; unknown: number; no_inviter: number };
  log_channel_id: string | null;
};

export function inviteTotal(row: Pick<InviteMember, "valid" | "left">) {
  return row.valid + row.left;
}

export function uncreditedCount(overview: Pick<InviteOverview, "uncredited">) {
  const item = overview.uncredited;
  return item.ambiguous + item.unknown + item.no_inviter;
}
