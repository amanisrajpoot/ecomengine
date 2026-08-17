"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import type { OrderDetail, PriceBreakdown } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Button, Card, OrderTimeline, PriceDisplay, StatusBadge } from "@commerce/ui";
import type { TimelineStep } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { formatOrderTime } from "@/lib/orderHelpers";
import { merchantTransitionsFor } from "@/lib/orderTransitions";

function pricingFromSnapshot(snapshot: Record<string, unknown>): PriceBreakdown | null {
  if (typeof snapshot.total_paise !== "number") return null;
  return snapshot as unknown as PriceBreakdown;
}

function timelineSteps(order: OrderDetail): TimelineStep[] {
  if (!order.status_events?.length) {
    return [{ id: order.status, label: order.status.replace(/_/g, " "), active: true }];
  }
  return order.status_events.map((event, index) => ({
    id: event.id,
    label: event.to_status.replace(/_/g, " "),
    time: formatOrderTime(event.created_at),
    done: index < order.status_events!.length - 1,
    active: index === order.status_events!.length - 1,
  }));
}

export default function MerchantOrderDetailPage() {
  const params = useParams<{ businessId: string; orderId: string }>();
  const { businessId, orderId } = params;

  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [transitioning, setTransitioning] = useState<string | null>(null);

  const loadOrder = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const detail = await getApiClient().getOrder(orderId);
      setOrder(detail);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load order");
    } finally {
      setLoading(false);
    }
  }, [orderId]);

  useEffect(() => {
    loadOrder();
  }, [loadOrder]);

  async function transition(toStatus: string) {
    setTransitioning(toStatus);
    setError(null);
    try {
      const updated = await getApiClient().transitionOrder(orderId, { to_status: toStatus });
      setOrder(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Transition failed");
    } finally {
      setTransitioning(null);
    }
  }

  const pricing = order ? pricingFromSnapshot(order.pricing_snapshot) : null;
  const nextStatuses = order
    ? merchantTransitionsFor(order.state_machine_profile, order.status)
    : [];
  const steps = useMemo(() => (order ? timelineSteps(order) : []), [order]);

  return (
    <div className="space-y-5">
      <Link
        href={`/business/${businessId}/orders`}
        className="text-sm font-medium text-[var(--brand)]"
      >
        ← Back to queue
      </Link>

      {loading ? <p className="text-sm text-gray-500">Loading…</p> : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      {order ? (
        <>
          <div className="rounded-2xl bg-white p-5 shadow-sm">
            <div className="flex items-start justify-between gap-3">
              <div>
                <StatusBadge status={order.status} />
                <p className="mt-2 font-mono text-xs text-gray-400">{order.id}</p>
                <p className="mt-1 text-sm text-gray-500">{order.state_machine_profile}</p>
              </div>
              {pricing ? (
                <PriceDisplay paise={pricing.total_paise} className="text-xl font-bold text-gray-900" />
              ) : null}
            </div>
          </div>

          {nextStatuses.length > 0 ? (
            <div className="space-y-2">
              {nextStatuses.map((status) => (
                <Button
                  key={status}
                  variant={status === "CANCELLED" ? "ghost" : "brand"}
                  className={
                    status === "CANCELLED"
                      ? "w-full border border-red-200 text-red-600 hover:bg-red-50"
                      : "w-full py-4 text-base font-bold"
                  }
                  disabled={transitioning !== null}
                  onClick={() => transition(status)}
                >
                  {transitioning === status
                    ? "Updating…"
                    : status === "CANCELLED"
                      ? "Cancel order"
                      : `Mark ${status.replace(/_/g, " ").toLowerCase()}`}
                </Button>
              ))}
            </div>
          ) : null}

          {order.items && order.items.length > 0 ? (
            <Card variant="light" title="Items">
              <ul className="divide-y divide-gray-100">
                {order.items.map((item) => (
                  <li key={item.id} className="flex justify-between gap-3 py-3 text-sm first:pt-0 last:pb-0">
                    <span className="font-medium text-gray-900">
                      {item.name_snapshot} <span className="text-gray-500">× {item.quantity}</span>
                    </span>
                    <PriceDisplay
                      paise={item.unit_price_paise * item.quantity}
                      className="text-gray-900"
                    />
                  </li>
                ))}
              </ul>
            </Card>
          ) : null}

          {steps.length > 0 ? (
            <Card variant="light" title="Timeline">
              <OrderTimeline steps={steps} />
            </Card>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
