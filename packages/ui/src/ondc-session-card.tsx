"use client";

import type { OndcSession } from "@commerce/types";
import { StatusBadge } from "@commerce/ui";

type OndcSessionCardProps = {
  session: OndcSession;
  className?: string;
};

export function OndcSessionCard({ session, className = "" }: OndcSessionCardProps) {
  return (
    <article
      className={`rounded-2xl border border-white/10 bg-black/20 px-4 py-4 ${className}`}
    >
      <div className="flex flex-wrap items-start justify-between gap-2">
        <div className="flex flex-wrap items-center gap-2">
          <StatusBadge status={session.stage} className="!text-[10px]" />
          <span className="text-xs uppercase tracking-wide text-white/45">ONDC</span>
        </div>
        <time className="text-xs text-white/40">
          {new Date(session.updated_at).toLocaleString("en-IN")}
        </time>
      </div>
      <p className="mt-3 font-mono text-sm text-white/80">{session.transaction_id}</p>
      <p className="mt-2 text-xs text-white/40">
        BAP {session.bap_id}
        {session.order_id ? ` · order ${session.order_id.slice(0, 8)}…` : ""}
        {session.cart_id && !session.order_id ? ` · cart ${session.cart_id.slice(0, 8)}…` : ""}
      </p>
      <p className="mt-1 text-xs text-white/35">
        {session.callback_log.length} callback{session.callback_log.length === 1 ? "" : "s"}
      </p>
    </article>
  );
}
