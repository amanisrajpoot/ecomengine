"use client";

import type { BusinessLocation } from "@commerce/types";

import { StatusBadge } from "./status-badge";

type LocationCardProps = {
  location: BusinessLocation;
  className?: string;
  href?: string;
};

function formatAddress(address: Record<string, unknown>): string {
  const line1 = typeof address.line1 === "string" ? address.line1 : "";
  const city = typeof address.city === "string" ? address.city : "";
  const pincode = typeof address.pincode === "string" ? address.pincode : "";
  return [line1, city, pincode].filter(Boolean).join(", ");
}

export function LocationCard({ location, className = "", href }: LocationCardProps) {
  const body = (
    <article
      className={`rounded-2xl border border-white/10 bg-black/20 px-4 py-4 transition hover:border-white/20 ${className}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-medium text-white/90">{location.name}</p>
          <p className="mt-1 text-sm text-white/50">{formatAddress(location.address)}</p>
          <p className="mt-1 text-xs text-white/35">
            {location.lat.toFixed(4)}, {location.lng.toFixed(4)}
          </p>
        </div>
        <StatusBadge
          status={location.is_active ? "ACTIVE" : "INACTIVE"}
          className="!text-[10px]"
        />
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
