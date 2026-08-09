"use client";

import type { Settlement } from "@commerce/types";
import { StatusBadge, formatPaise } from "@commerce/ui";
import type { ReactNode } from "react";

type SettlementCardProps = {
  settlement: Settlement;
  partyLabel?: string;
  href?: string;
  actions?: ReactNode;
  className?: string;
};

export function SettlementCard({
  settlement,
  partyLabel,
  href,
  actions,
  className = "",
}: SettlementCardProps) {
  const content = (
    <>
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={settlement.status} />
            <span className="text-xs uppercase tracking-wide text-white/45">
              {settlement.party_type}
            </span>
          </div>
          <p className="mt-2 text-sm text-white/70">
            {partyLabel ?? settlement.party_id.slice(0, 8)}…
          </p>
        </div>
        <p className="font-display text-2xl text-white">{formatPaise(settlement.total_paise)}</p>
      </div>
      <p className="mt-3 text-xs text-white/40">
        {new Date(settlement.period_start).toLocaleDateString("en-IN")} –{" "}
        {new Date(settlement.period_end).toLocaleDateString("en-IN")} ·{" "}
        {settlement.ledger_entry_ids.length} ledger entries
      </p>
      {actions ? <div className="mt-4">{actions}</div> : null}
    </>
  );

  const shellClass = `block rounded-2xl border border-white/10 bg-black/20 px-4 py-4 transition ${className}`;

  if (href) {
    return (
      <a href={href} className={`${shellClass} hover:border-white/20`}>
        {content}
      </a>
    );
  }

  return <section className={shellClass}>{content}</section>;
}
