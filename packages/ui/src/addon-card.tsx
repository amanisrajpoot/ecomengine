"use client";

import type { ReactNode } from "react";
import type { Addon } from "@commerce/types";

import { formatPaise } from "./format";
import { StatusBadge } from "./status-badge";

type AddonCardProps = {
  addon: Addon;
  className?: string;
  actions?: ReactNode;
};

export function AddonCard({ addon, className = "", actions }: AddonCardProps) {
  return (
    <article
      className={`flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-black/15 px-4 py-3 ${className}`}
    >
      <div>
        <p className="text-sm font-medium text-white/85">{addon.name}</p>
        <p className="mt-1 text-xs text-white/45">
          {formatPaise(addon.price_paise)} · max {addon.max_qty}
        </p>
      </div>
      <div className="flex items-center gap-2">
        <StatusBadge
          status={addon.is_active ? "ACTIVE" : "INACTIVE"}
          className="!text-[10px]"
        />
        {actions}
      </div>
    </article>
  );
}
