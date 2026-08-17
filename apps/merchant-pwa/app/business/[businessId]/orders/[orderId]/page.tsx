"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import type { OrderDetail, PriceBreakdown } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Button, Card, PriceDisplay } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { merchantTransitionsFor } from "@/lib/orderTransitions";

function pricingFromSnapshot(snapshot: Record<string, unknown>): PriceBreakdown | null {
  if (typeof snapshot.total_paise !== "number") return null;
  return snapshot as unknown as PriceBreakdown;
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

  return (
    <div className="space-y-4">
      <Link
        href={`/business/${businessId}/orders`}
        className="text-xs text-amber-300/70 hover:text-amber-100"
      >
        ← Orders
      </Link>
      <h1 className="text-2xl font-semibold">Order detail</h1>
      {loading ? <p className="text-sm text-amber-200/60">Loading…</p> : null}
      {error ? <p className="text-sm text-red-300">{error}</p> : null}

      {order ? (
        <>
          <Card title="Status">
            <p className="text-lg font-medium">{order.status}</p>
            <p className="mt-1 text-xs font-mono text-amber-300/60">{order.id}</p>
            <p className="text-sm text-amber-200/70 mt-2">{order.state_machine_profile}</p>
          </Card>

          {pricing ? (
            <Card title="Total">
              <PriceDisplay paise={pricing.total_paise} className="text-lg" />
            </Card>
          ) : null}

          {order.items && order.items.length > 0 ? (
            <Card title="Items">
              <ul className="space-y-2 text-sm">
                {order.items.map((item) => (
                  <li key={item.id} className="flex justify-between gap-2">
                    <span>{item.name_snapshot} × {item.quantity}</span>
                    <PriceDisplay paise={item.unit_price_paise * item.quantity} />
                  </li>
                ))}
              </ul>
            </Card>
          ) : null}

          {nextStatuses.length > 0 ? (
            <Card title="Actions">
              <div className="flex flex-wrap gap-2">
                {nextStatuses.map((status) => (
                  <Button
                    key={status}
                    variant={status === "CANCELLED" ? "ghost" : "primary"}
                    disabled={transitioning !== null}
                    onClick={() => transition(status)}
                  >
                    {transitioning === status ? "…" : status.replace(/_/g, " ")}
                  </Button>
                ))}
              </div>
            </Card>
          ) : null}

          {order.status_events && order.status_events.length > 0 ? (
            <Card title="Timeline">
              <ul className="space-y-1 text-sm text-amber-200/80">
                {order.status_events.map((event) => (
                  <li key={event.id}>
                    {event.to_status}{" "}
                    <span className="text-amber-400/60">{event.created_at}</span>
                  </li>
                ))}
              </ul>
            </Card>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
