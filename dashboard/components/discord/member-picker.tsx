"use client";

import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { Input } from "@/components/ui/input";

export type MemberChoice = { id: string; display_name: string; username?: string; avatar?: string };

export function MemberPicker({
  guildId,
  onSelect,
}: {
  guildId: string;
  onSelect: (member: MemberChoice) => void;
}) {
  const [query, setQuery] = useState("");
  const [members, setMembers] = useState<MemberChoice[]>([]);

  useEffect(() => {
    const needle = query.trim();
    if (needle.length < 2) {
      setMembers([]);
      return;
    }
    const timer = window.setTimeout(() => {
      api.searchTicketMembers(guildId, needle).then((body) => setMembers(body.members ?? [])).catch(() => setMembers([]));
    }, 200);
    return () => window.clearTimeout(timer);
  }, [guildId, query]);

  return (
    <div className="space-y-1">
      <Input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search members" aria-label="Search members" />
      {members.length > 0 && (
        <ul className="border border-line-subtle">
          {members.map((member) => (
            <li key={member.id}>
              <button type="button" className="flex w-full items-center gap-2 px-2 py-1.5 text-left text-small hover:bg-surface-2" onClick={() => onSelect(member)}>
                {member.avatar ? <img src={member.avatar} alt="" className="size-5 rounded-full" /> : <span className="size-5 rounded-full bg-surface-2" />}
                <span>{member.display_name}</span>
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
