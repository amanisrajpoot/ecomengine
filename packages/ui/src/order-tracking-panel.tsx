"use client";

import { ApiError } from "@commerce/api-client";
import type { Delivery, Fulfillment, Order } from "@commerce/types";
import { StatusBadge } from "@commerce/ui";
import { useCallback, useEffect, useState } from "react";

type TrackingApi = {
  getOrderFulfillment: (orderId: string) => Promise<Fulfillment>;
  getFulfillmentDelivery: (fulfillmentId: string) => Promise<Delivery>;
};

type OrderTrackingPanelProps = {
  order: Order;
  api: TrackingApi;
  className?: string;
};

const TRACKABLE = new Set([
  "ACCEPTED",
  "PREPARING",
  "PICKING",
  "PACKING",
  "READY",
  "PICKED_UP",
  "OUT_FOR_DELIVERY",
  "IN_TRANSIT",
  "PAYMENT_CONFIRMED",
  "PICKUP_ASSIGNED",
  "DELIVERED",
]);

export function OrderTrackingPanel({ order, api, className = "" }: OrderTrackingPanelProps) {
  const [fulfillment, setFulfillment] = useState<Fulfillment | null>(null);
  const [delivery, setDelivery] = useState<Delivery | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    if (order.fulfillment_type === "SELF_PICKUP") {
      setLoading(false);
      return;
    }
    if (!TRACKABLE.has(order.status) && order.state_machine_profile !== "COURIER") {
      setLoading(false);
      return;
    }

    try {
      const ful = await api.getOrderFulfillment(order.id);
      setFulfillment(ful);
      try {
        const del = await api.getFulfillmentDelivery(ful.id);
        setDelivery(del);
      } catch (err) {
        if (!(err instanceof ApiError && err.status === 404)) {
          throw err;
        }
        setDelivery(null);
      }
      setError(null);
    } catch (err) {
      if (!(err instanceof ApiError && err.status === 404)) {
        setError(err instanceof ApiError ? err.message : "Could not load tracking");
      }
    } finally {
      setLoading(false);
    }
  }, [api, order.fulfillment_type, order.id, order.state_machine_profile, order.status]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (order.fulfillment_type === "SELF_PICKUP") return;
    if (!TRACKABLE.has(order.status) && order.status !== "DELIVERED") return;
    const timer = window.setInterval(() => {
      void load();
    }, 5000);
    return () => window.clearInterval(timer);
  }, [load, order.fulfillment_type, order.status]);

  if (order.fulfillment_type === "SELF_PICKUP") return null;
  if (
    order.state_machine_profile !== "COURIER" &&
    !TRACKABLE.has(order.status) &&
    order.status !== "DELIVERED"
  ) {
    return null;
  }

  const dropAddress =
    typeof order.metadata?.drop === "object" && order.metadata.drop
      ? (order.metadata.drop as { address?: { line1?: string; city?: string } }).address
      : null;

  return (
    <section
      className={`rounded-2xl border border-emerald-200/10 bg-emerald-950/30 px-4 py-4 ${className}`}
    >
      <p className="text-sm font-medium text-emerald-50">Delivery tracking</p>
      {dropAddress?.line1 ? (
        <p className="mt-1 text-xs text-emerald-100/50">
          {dropAddress.line1}
          {dropAddress.city ? `, ${dropAddress.city}` : ""}
        </p>
      ) : null}

      {loading ? (
        <p className="mt-3 text-sm text-emerald-100/45">Loading tracking…</p>
      ) : (
        <div className="mt-3 space-y-2 text-sm text-emerald-100/75">
          {fulfillment ? (
            <p>
              Fulfillment <StatusBadge status={fulfillment.status} className="!text-[10px]" />
            </p>
          ) : null}
          {delivery ? (
            <>
              <p>
                Delivery <StatusBadge status={delivery.status} className="!text-[10px]" />
              </p>
              {delivery.partner_id ? (
                <p className="text-xs text-emerald-200/70">Rider assigned — on the way</p>
              ) : (
                <p className="text-xs text-amber-200/70">Finding a rider…</p>
              )}
            </>
          ) : fulfillment ? (
            <p className="text-xs text-emerald-100/45">Rider will be assigned when your order is ready.</p>
          ) : null}
        </div>
      )}

      {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
      {!loading && order.status !== "DELIVERED" && order.status !== "CANCELLED" ? (
        <p className="mt-3 text-xs text-emerald-100/35">Updates every 5 seconds.</p>
      ) : null}
    </section>
  );
}
