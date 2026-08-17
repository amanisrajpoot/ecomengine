export type TimelineStep = {
  id: string;
  label: string;
  time?: string;
  active?: boolean;
  done?: boolean;
};

export type OrderTimelineProps = {
  steps: TimelineStep[];
};

export function OrderTimeline({ steps }: OrderTimelineProps) {
  return (
    <ol className="space-y-0">
      {steps.map((step, index) => {
        const isLast = index === steps.length - 1;
        return (
          <li key={step.id} className="flex gap-3">
            <div className="flex flex-col items-center">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-full text-xs font-bold ${
                  step.done
                    ? "bg-emerald-500 text-white"
                    : step.active
                      ? "bg-orange-500 text-white"
                      : "bg-gray-200 text-gray-500"
                }`}
              >
                {step.done ? "✓" : index + 1}
              </div>
              {!isLast ? <div className="my-1 w-0.5 flex-1 bg-gray-200 min-h-[24px]" /> : null}
            </div>
            <div className="pb-6">
              <p className={`text-sm font-medium ${step.active || step.done ? "text-gray-900" : "text-gray-500"}`}>
                {step.label}
              </p>
              {step.time ? <p className="text-xs text-gray-400">{step.time}</p> : null}
            </div>
          </li>
        );
      })}
    </ol>
  );
}
