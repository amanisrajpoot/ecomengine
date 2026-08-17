import { formatPaise } from "./format";

export type PriceDisplayProps = {
  paise: number;
  currency?: string;
  className?: string;
};

export function PriceDisplay({ paise, currency = "INR", className = "" }: PriceDisplayProps) {
  return (
    <span className={`tabular-nums font-medium ${className || "text-emerald-100"}`}>
      {formatPaise(paise, currency)}
    </span>
  );
}
