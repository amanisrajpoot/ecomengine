import Link from "next/link";

import type { Order } from "@commerce/types";
import { PriceDisplay, StatusBadge } from "@commerce/ui";

import {
  formatOrderTime,
  orderNeedsMerchantAction,
  orderTotalPaise,
  primaryMerchantAction,
} from "@/lib/orderHelpers";

type OrderQueueCardProps = {
  order: Order;
  businessId: string;
};

export function OrderQueueCard({ order, businessId }: OrderQueueCardProps) {
  const needsAction = orderNeedsMerchantAction(order.state_machine_profile, order.status);
  const nextAction = primaryMerchantAction(order.state_machine_profile, order.status);
  const total = orderTotalPaise(order);

  return (
    <Link href={`/business/${businessId}/orders/${order.id}`} className="block">
      <article
        className={`rounded-2xl border bg-white p-4 shadow-sm transition-shadow hover:shadow-md ${
          needsAction ? "border-orange-300 ring-1 ring-orange-200" : "border-gray-200"
        }`}
      >
        <div className="flex items-start justify-between gap-3">
          <div className="space-y-1">
            <StatusBadge status={order.status} />
            <p className="font-mono text-xs text-gray-400">{order.id.slice(0, 8)}…</p>
          </div>
          {total !== null ? (
            <PriceDisplay paise={total} className="text-base font-bold text-gray-900" />
          ) : null}
        </div>

        <p className="mt-3 text-xs text-gray-500">
          {formatOrderTime(order.placed_at ?? order.created_at)}
        </p>

        {needsAction && nextAction ? (
          <p className="mt-3 rounded-lg bg-orange-50 px-3 py-2 text-sm font-semibold text-orange-700">
            Tap to {nextAction.replace(/_/g, " ").toLowerCase()}
          </p>
        ) : null}
      </article>
    </Link>
  );
}
