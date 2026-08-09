"use client";

import type { LedgerEntry } from "@commerce/types";
import { formatPaise, StatusBadge } from "@commerce/ui";
import Link from "next/link";

type LedgerEntryCardProps = {
  entry: LedgerEntry;
  eventHref?: string;
  className?: string;
};

export function LedgerEntryCard({ entry, eventHref, className = "" }: LedgerEntryCardProps) {
  return (
    <article
      className={`rounded-2xl border border-white/10 bg-black/20 px-4 py-4 ${className}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={entry.direction} className="!text-[10px]" />
          <span className="text-xs uppercase tracking-wide text-white/45">{entry.account}</span>
        </div>
        <p className="font-display text-lg text-white">{formatPaise(entry.amount_paise)}</p>
      </div>
      <p className="mt-2 text-xs text-white/40">
        {entry.event_type} · {entry.reference_key}
      </p>
      <div className="mt-2 flex flex-wrap items-center gap-2 text-xs text-white/35">
        <time>{new Date(entry.created_at).toLocaleString("en-IN")}</time>
        {entry.order_id ? <span>· order {entry.order_id.slice(0, 8)}…</span> : null}
        {eventHref ? (
          <Link href={eventHref} className="text-violet-300/80 hover:text-violet-100">
            View event
          </Link>
        ) : null}
      </div>
    </article>
  );
}
