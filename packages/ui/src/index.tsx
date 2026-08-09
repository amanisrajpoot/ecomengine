import type { ButtonHTMLAttributes, InputHTMLAttributes, ReactNode } from "react";

export { formatPaise } from "./format";
export { Spinner } from "./spinner";
export { EmptyState } from "./empty-state";
export { StatusBadge } from "./status-badge";
export { PriceBreakdown, type PricingSnapshot } from "./price-breakdown";
export { OrderStatusStepper } from "./order-status-stepper";
export { DispatchPanel } from "./dispatch-panel";
export { OrderTrackingPanel } from "./order-tracking-panel";
export { SettlementCard } from "./settlement-card";
export { PaymentPanel } from "./payment-panel";
export { flowStepsFor, statusLabel, ORDER_FLOW_STEPS } from "./order-flow";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "ghost" | "soft";
  children: ReactNode;
};

export function Button({
  variant = "primary",
  className = "",
  children,
  ...props
}: ButtonProps) {
  const styles =
    variant === "primary"
      ? "bg-emerald-500 text-emerald-950 hover:bg-emerald-400"
      : variant === "soft"
        ? "bg-emerald-400/15 text-emerald-50 hover:bg-emerald-400/25"
        : "bg-transparent text-emerald-50/90 hover:bg-white/5";
  return (
    <button
      className={`inline-flex items-center justify-center rounded-xl px-4 py-2.5 text-sm font-medium transition duration-200 disabled:opacity-50 ${styles} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

type FieldProps = InputHTMLAttributes<HTMLInputElement> & {
  label: string;
};

export function TextField({ label, className = "", id, ...props }: FieldProps) {
  const fieldId = id ?? props.name ?? label.toLowerCase().replace(/\s+/g, "-");
  return (
    <label className="flex flex-col gap-1.5 text-sm text-emerald-50/80">
      <span>{label}</span>
      <input
        id={fieldId}
        className={`rounded-xl border border-emerald-200/15 bg-emerald-950/40 px-3 py-2.5 text-emerald-50 outline-none ring-emerald-400/40 placeholder:text-emerald-100/35 focus:ring-2 ${className}`}
        {...props}
      />
    </label>
  );
}
