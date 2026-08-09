import { flowStepsFor, statusLabel } from "./order-flow";

type OrderStatusStepperProps = {
  profile: string;
  status: string;
  className?: string;
};

export function OrderStatusStepper({ profile, status, className = "" }: OrderStatusStepperProps) {
  const steps = flowStepsFor(profile);
  const current = ["CREATED", "PAYMENT_PENDING"].includes(status)
    ? -1
    : steps.indexOf(status);
  const isTerminal = ["CANCELLED", "FAILED", "REFUNDED"].includes(status);
  const isDelivered = status === "DELIVERED";

  if (isTerminal) {
    return (
      <div className={`rounded-xl border border-rose-400/25 bg-rose-950/30 px-4 py-3 text-sm text-rose-200 ${className}`}>
        Order {statusLabel(status).toLowerCase()}
      </div>
    );
  }

  return (
    <ol className={`flex flex-col gap-0 sm:flex-row sm:items-start sm:gap-0 ${className}`}>
      {steps.map((step, index) => {
        const done = isDelivered ? true : current > index;
        const active = !isDelivered && current === index;
        const upcoming = !isDelivered && current < index;
        return (
          <li key={step} className="flex flex-1 items-start gap-2 sm:flex-col sm:items-center sm:gap-1">
            <div className="flex items-center gap-2 sm:flex-col">
              <span
                className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold ${
                  done
                    ? "bg-emerald-500 text-emerald-950"
                    : active
                      ? "bg-white text-black ring-2 ring-white/40"
                      : "bg-white/10 text-white/40"
                }`}
              >
                {done ? "✓" : index + 1}
              </span>
              {index < steps.length - 1 ? (
                <span
                  className={`hidden h-0.5 flex-1 sm:block sm:h-auto sm:w-full sm:flex-none sm:self-center sm:border-t-2 ${
                    done ? "border-emerald-500/60" : "border-white/10"
                  }`}
                  aria-hidden
                />
              ) : null}
            </div>
            <p
              className={`pb-4 text-xs sm:pb-0 sm:text-center ${
                active ? "font-medium text-white" : upcoming ? "text-white/35" : "text-white/60"
              }`}
            >
              {statusLabel(step)}
            </p>
          </li>
        );
      })}
    </ol>
  );
}
