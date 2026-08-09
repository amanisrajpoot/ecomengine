"use client";

import type { ReactNode } from "react";
import type { Product, Variant } from "@commerce/types";

import { formatPaise } from "./format";
import { StatusBadge } from "./status-badge";

type ProductCardProps = {
  product: Product;
  variantCount?: number;
  minPricePaise?: number | null;
  categoryName?: string | null;
  className?: string;
  href?: string;
};

export function ProductCard({
  product,
  variantCount,
  minPricePaise,
  categoryName,
  className = "",
  href,
}: ProductCardProps) {
  const body = (
    <article
      className={`rounded-2xl border border-white/10 bg-black/20 px-4 py-4 transition hover:border-white/20 ${className}`}
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="font-medium text-white/90">{product.name}</p>
          {categoryName ? (
            <p className="mt-1 text-xs uppercase tracking-wide text-white/40">{categoryName}</p>
          ) : null}
        </div>
        <StatusBadge
          status={product.is_active ? "ACTIVE" : "INACTIVE"}
          className="!text-[10px]"
        />
      </div>
      {product.description ? (
        <p className="mt-2 line-clamp-2 text-sm text-white/55">{product.description}</p>
      ) : null}
      <div className="mt-3 flex flex-wrap gap-3 text-xs text-white/45">
        {variantCount != null ? <span>{variantCount} variant{variantCount === 1 ? "" : "s"}</span> : null}
        {minPricePaise != null ? <span>from {formatPaise(minPricePaise)}</span> : null}
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

type VariantRowProps = {
  variant: Variant;
  className?: string;
  actions?: ReactNode;
};

export function VariantRow({ variant, className = "", actions }: VariantRowProps) {
  return (
    <div
      className={`flex flex-wrap items-center justify-between gap-3 rounded-xl border border-white/10 bg-black/15 px-4 py-3 ${className}`}
    >
      <div>
        <p className="text-sm font-medium text-white/85">{variant.name}</p>
        <p className="mt-1 text-xs text-white/45">
          {variant.sku ? `SKU ${variant.sku} · ` : ""}
          {formatPaise(variant.base_price_paise)}
        </p>
      </div>
      <div className="flex items-center gap-2">
        <StatusBadge
          status={variant.is_available ? "AVAILABLE" : "UNAVAILABLE"}
          className="!text-[10px]"
        />
        {actions}
      </div>
    </div>
  );
}
