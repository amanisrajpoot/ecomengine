"use client";

import type { Partner } from "@commerce/types";

import { StatusBadge } from "./status-badge";

type PartnerCardProps = {
  partner: Partner;
  className?: string;
  href?: string;
  subtitle?: string;
};

export function PartnerCard({ partner, className = "", href, subtitle }: PartnerCardProps) {
  const label = partner.display_name ?? `Rider ${partner.id.slice(0, 8)}…`;
  const body = (
    <article
      className={`rounded-2xl border border-white/10 bg-black/20 px-4 py-4 transition hover:border-white/20 ${className}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-medium text-white/90">{label}</p>
          {subtitle ? <p className="mt-1 text-xs text-white/45">{subtitle}</p> : null}
          {partner.current_lat != null && partner.current_lng != null ? (
            <p className="mt-1 text-xs text-white/35">
              {partner.current_lat.toFixed(4)}, {partner.current_lng.toFixed(4)}
            </p>
          ) : null}
        </div>
        <div className="flex flex-col items-end gap-1">
          <StatusBadge status={partner.status} className="!text-[10px]" />
          <span
            className={`inline-flex items-center gap-1 text-[10px] uppercase tracking-wide ${
              partner.is_online ? "text-emerald-300" : "text-white/35"
            }`}
          >
            <span
              className={`h-1.5 w-1.5 rounded-full ${
                partner.is_online ? "bg-emerald-400" : "bg-white/25"
              }`}
            />
            {partner.is_online ? "Online" : "Offline"}
          </span>
        </div>
      </div>
    </article>
  );

  if (href) {
    return (
      <a href={href} className="block">
        {body}
      </a>
    );
  }
  return body;
}
