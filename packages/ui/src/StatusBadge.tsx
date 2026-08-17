const STATUS_STYLES: Record<string, string> = {
  PAYMENT_CONFIRMED: "bg-blue-100 text-blue-800",
  ACCEPTED: "bg-orange-100 text-orange-800",
  PREPARING: "bg-amber-100 text-amber-900",
  PICKING: "bg-amber-100 text-amber-900",
  READY: "bg-emerald-100 text-emerald-800",
  OUT_FOR_DELIVERY: "bg-indigo-100 text-indigo-800",
  DELIVERED: "bg-gray-100 text-gray-600",
  CANCELLED: "bg-red-100 text-red-700",
  ACTIVE: "bg-emerald-100 text-emerald-800",
  INACTIVE: "bg-gray-100 text-gray-600",
};

export type StatusBadgeProps = {
  status: string;
  className?: string;
};

export function StatusBadge({ status, className = "" }: StatusBadgeProps) {
  const label = status.replace(/_/g, " ");
  const style = STATUS_STYLES[status] ?? "bg-gray-100 text-gray-700";

  return (
    <span
      className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold uppercase tracking-wide ${style} ${className}`}
    >
      {label}
    </span>
  );
}
