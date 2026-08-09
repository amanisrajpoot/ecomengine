import { statusLabel } from "./order-flow";

type StatusBadgeProps = {
  status: string;
  className?: string;
};

function toneFor(status: string): string {
  if (["DELIVERED", "COMPLETED"].includes(status)) {
    return "bg-emerald-400/20 text-emerald-100 ring-emerald-400/30";
  }
  if (["CANCELLED", "FAILED", "REFUNDED"].includes(status)) {
    return "bg-rose-400/15 text-rose-200 ring-rose-400/25";
  }
  if (["PAYMENT_CONFIRMED", "ACCEPTED", "READY", "PICKUP_ASSIGNED"].includes(status)) {
    return "bg-sky-400/15 text-sky-100 ring-sky-400/25";
  }
  if (["PREPARING", "PICKING", "PICKED_UP", "OUT_FOR_DELIVERY", "IN_TRANSIT"].includes(status)) {
    return "bg-amber-400/15 text-amber-100 ring-amber-400/25";
  }
  return "bg-white/10 text-white/70 ring-white/15";
}

export function StatusBadge({ status, className = "" }: StatusBadgeProps) {
  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium uppercase tracking-wide ring-1 ring-inset ${toneFor(status)} ${className}`}
    >
      {statusLabel(status)}
    </span>
  );
}
