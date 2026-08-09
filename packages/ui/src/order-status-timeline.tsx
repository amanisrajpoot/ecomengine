"use client";

import type { Order } from "@commerce/types";

type OrderStatusTimelineProps = {
  events: NonNullable<Order["status_events"]>;
  className?: string;
};

export function OrderStatusTimeline({ events, className = "" }: OrderStatusTimelineProps) {
  if (!events.length) return null;

  return (
    <section
      className={`rounded-2xl border border-white/10 bg-black/20 px-4 py-4 ${className}`}
    >
      <p className="text-sm font-medium text-white/90">Status history</p>
      <ol className="mt-3 space-y-2">
        {events.map((event, index) => (
          <li key={`${event.to_status}-${event.created_at}-${index}`} className="text-xs text-white/50">
            <span className="text-white/75">
              {event.from_status ?? "—"} → {event.to_status}
            </span>
            {event.actor_role ? (
              <span className="text-white/35"> · {event.actor_role}</span>
            ) : null}
            <span className="block text-[10px] text-white/30">
              {new Date(event.created_at).toLocaleString("en-IN")}
            </span>
          </li>
        ))}
      </ol>
    </section>
  );
}
