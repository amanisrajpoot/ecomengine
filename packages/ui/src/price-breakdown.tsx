import { formatPaise } from "./format";

export type PricingSnapshot = {
  subtotal_paise?: number;
  discount_paise?: number;
  delivery_fee_paise?: number;
  platform_fee_paise?: number;
  other_fees_paise?: number;
  tax_paise?: number;
  total_paise?: number;
};

type PriceBreakdownProps = {
  snapshot: PricingSnapshot | Record<string, unknown> | null | undefined;
  className?: string;
};

function row(label: string, paise: number | undefined, muted = false) {
  if (paise == null || paise === 0) return null;
  return (
    <div className={`flex justify-between text-sm ${muted ? "text-white/45" : "text-white/70"}`}>
      <span>{label}</span>
      <span>{formatPaise(paise)}</span>
    </div>
  );
}

export function PriceBreakdown({ snapshot, className = "" }: PriceBreakdownProps) {
  const s = (snapshot ?? {}) as PricingSnapshot;
  const total = s.total_paise;

  return (
    <div className={`space-y-2 rounded-2xl border border-white/10 bg-black/20 px-4 py-3 ${className}`}>
      {row("Subtotal", s.subtotal_paise, true)}
      {row("Discount", s.discount_paise ? -s.discount_paise : undefined, true)}
      {row("Delivery fee", s.delivery_fee_paise, true)}
      {row("Platform fee", s.platform_fee_paise, true)}
      {row("Other fees", s.other_fees_paise, true)}
      {row("Tax", s.tax_paise, true)}
      <div className="flex justify-between border-t border-white/10 pt-2 text-base font-medium text-white">
        <span>Total</span>
        <span>{total != null ? formatPaise(total) : "—"}</span>
      </div>
    </div>
  );
}
