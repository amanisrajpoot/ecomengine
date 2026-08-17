import type { ReactNode } from "react";

import { Badge } from "./Badge";

export type BusinessCardProps = {
  name: string;
  type: string;
  description?: string | null;
  etaLabel?: string;
  href?: string;
  onClick?: () => void;
  children?: ReactNode;
};

const typeEmoji: Record<string, string> = {
  FOOD: "🍽️",
  GROCERY: "🛒",
  RETAIL: "🏪",
  COURIER: "📦",
};

export function BusinessCard({
  name,
  type,
  description,
  etaLabel = "25–35 min",
  children,
}: BusinessCardProps) {
  const emoji = typeEmoji[type] ?? "🏷️";
  return (
    <article className="overflow-hidden rounded-2xl border border-gray-100 bg-white shadow-sm transition hover:shadow-md">
      <div className="flex h-28 items-center justify-center bg-gradient-to-br from-orange-50 to-amber-50 text-4xl">
        {emoji}
      </div>
      <div className="space-y-2 p-4">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold text-gray-900 leading-tight">{name}</h3>
          <Badge variant="accent">{type}</Badge>
        </div>
        {description ? (
          <p className="line-clamp-2 text-sm text-gray-500">{description}</p>
        ) : null}
        <p className="text-xs font-medium text-emerald-600">{etaLabel} · Free delivery*</p>
        {children}
      </div>
    </article>
  );
}
