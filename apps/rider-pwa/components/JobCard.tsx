import Link from "next/link";

import type { Delivery } from "@commerce/types";
import { StatusBadge } from "@commerce/ui";

import {
  deliveryNeedsAction,
  formatTime,
  nextPendingStop,
  stopsCompletedCount,
  stopsTotalCount,
} from "@/lib/deliveryHelpers";

type JobCardProps = {
  delivery: Delivery;
};

export function JobCard({ delivery }: JobCardProps) {
  const needsAction = deliveryNeedsAction(delivery);
  const completed = stopsCompletedCount(delivery);
  const total = stopsTotalCount(delivery);
  const nextStop = nextPendingStop(delivery);

  return (
    <Link href={`/jobs/${delivery.id}`} className="block">
      <article
        className={`rounded-2xl border bg-white p-4 shadow-sm transition-shadow hover:shadow-md ${
          needsAction ? "border-blue-300 ring-1 ring-blue-200" : "border-gray-200"
        }`}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <StatusBadge status={delivery.status} />
            <p className="font-mono text-xs text-gray-400">{delivery.id.slice(0, 8)}…</p>
          </div>
          <div className="text-right">
            <p className="text-sm font-bold text-gray-900">
              {completed}/{total} stops
            </p>
            <p className="text-xs text-gray-500">completed</p>
          </div>
        </div>

        {delivery.eta ? (
          <p className="mt-3 text-xs text-gray-500">ETA {formatTime(delivery.eta)}</p>
        ) : (
          <p className="mt-3 text-xs text-gray-500">{formatTime(delivery.created_at)}</p>
        )}

        {needsAction && nextStop ? (
          <p className="mt-3 rounded-lg bg-blue-50 px-3 py-2 text-sm font-semibold text-blue-700">
            Next: {nextStop.stop_type.replace(/_/g, " ").toLowerCase()} stop
          </p>
        ) : null}
      </article>
    </Link>
  );
}
