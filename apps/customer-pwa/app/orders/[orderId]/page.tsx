"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import type { OrderDetail, Payment, PriceBreakdown } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { OrderTimeline, PriceDisplay, Skeleton } from "@commerce/ui";

import { getApiClient } from "@/lib/api";

function pricingFromSnapshot(snapshot: Record<string, unknown>): PriceBreakdown | null {
  if (!snapshot || typeof snapshot.total_paise !== "number") return null;
  return snapshot as unknown as PriceBreakdown;
}

export default function OrderDetailPage() {
  const params = useParams<{ orderId: string }>();
  const orderId = params.orderId;

  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        const api = getApiClient();
        const detail = await api.getOrder(orderId);
        setOrder(detail);
        const paymentList = await api.listOrderPayments(orderId);
        setPayments(paymentList);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load order");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [orderId]);

  const pricing = order ? pricingFromSnapshot(order.pricing_snapshot) : null;

  const timelineSteps = useMemo(() => {
    if (!order?.status_events?.length) return [];
    const events = order.status_events;
    return events.map((event, index) => ({
      id: event.id,
      label: event.to_status.replace(/_/g, " "),
      time: new Date(event.created_at).toLocaleString(),
      done: index < events.length - 1 || order.status === "DELIVERED",
      active: index === events.length - 1,
    }));
  }, [order]);

  return (
    <div className="space-y-4">
      <Link href="/orders" className="text-sm font-medium text-[var(--brand)]">← Orders</Link>

      {loading ? <Skeleton className="h-32" /> : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      {order ? (
        <>
          <div className="rounded-2xl bg-white p-4 shadow-sm">
            <p className="text-xs font-medium uppercase tracking-wide text-gray-400">Live status</p>
            <p className="mt-1 text-2xl font-bold text-gray-900">{order.status.replace(/_/g, " ")}</p>
            {pricing ? (
              <p className="mt-2 text-lg">
                <PriceDisplay paise={pricing.total_paise} className="!text-[var(--brand)] font-bold" />
              </p>
            ) : null}
          </div>

          {timelineSteps.length > 0 ? (
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <h2 className="mb-4 text-sm font-semibold text-gray-900">Tracking</h2>
              <OrderTimeline steps={timelineSteps} />
            </div>
          ) : null}

          {order.items && order.items.length > 0 ? (
            <div className="rounded-2xl bg-white p-4 shadow-sm">
              <h2 className="mb-3 text-sm font-semibold text-gray-900">Items</h2>
              <ul className="space-y-2 text-sm">
                {order.items.map((item) => (
                  <li key={item.id} className="flex justify-between gap-2 text-gray-700">
                    <span>{item.name_snapshot} × {item.quantity}</span>
                    <PriceDisplay paise={item.unit_price_paise * item.quantity} />
                  </li>
                ))}
              </ul>
            </div>
          ) : null}

          {payments.length > 0 ? (
            <div className="rounded-2xl bg-white p-4 shadow-sm text-sm text-gray-600">
              Payment: {payments[0].provider} · {payments[0].status}
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
