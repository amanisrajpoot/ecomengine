"use client";

import type { StaffMember } from "@commerce/types";

import { StatusBadge } from "./status-badge";

type StaffCardProps = {
  member: StaffMember;
  className?: string;
};

function contactLabel(member: StaffMember): string {
  if (member.display_name) return member.display_name;
  if (member.email) return member.email;
  if (member.phone) return member.phone;
  return `User ${member.user_id.slice(0, 8)}…`;
}

export function StaffCard({ member, className = "" }: StaffCardProps) {
  const subtitle =
    member.display_name && (member.email || member.phone)
      ? member.email ?? member.phone ?? null
      : member.email && member.phone
        ? member.phone
        : null;

  return (
    <article
      className={`rounded-2xl border border-white/10 bg-black/20 px-4 py-4 ${className}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-medium text-white/90">{contactLabel(member)}</p>
          {subtitle ? <p className="mt-1 text-xs text-white/45">{subtitle}</p> : null}
          <p className="mt-1 text-xs text-white/30">ID {member.user_id.slice(0, 8)}…</p>
        </div>
        <StatusBadge status={member.role} className="!text-[10px]" />
      </div>
    </article>
  );
}
