"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import type { OrderDetail, Payment, PriceBreakdown } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Card, PriceDisplay } from "@commerce/ui";

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

  return (
    <div className="space-y-4">
      <div>
        <Link href="/orders" className="text-xs text-emerald-300/70 hover:text-emerald-100">
          ← Orders
        </Link>
        <h1 className="mt-1 text-2xl font-semibold">Order</h1>
      </div>

      {loading ? <p className="text-sm text-emerald-200/60">Loading…</p> : null}
      {error ? <p className="text-sm text-red-300">{error}</p> : null}

      {order ? (
        <>
          <Card title="Status">
            <p className="text-lg font-medium">{order.status}</p>
            <p className="mt-1 text-xs text-emerald-200/60 font-mono">{order.id}</p>
            <p className="text-sm text-emerald-200/70 mt-2">
              Profile: {order.state_machine_profile} · {order.fulfillment_type}
            </p>
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
                    <span>
                      {item.name_snapshot} × {item.quantity}
                    </span>
                    <PriceDisplay paise={item.unit_price_paise * item.quantity} />
                  </li>
                ))}
              </ul>
            </Card>
          ) : null}

          {payments.length > 0 ? (
            <Card title="Payments">
              <ul className="space-y-2 text-sm">
                {payments.map((payment) => (
                  <li key={payment.id} className="flex justify-between gap-2">
                    <span>{payment.provider} — {payment.status}</span>
                    <PriceDisplay paise={payment.amount_paise} />
                  </li>
                ))}
              </ul>
            </Card>
          ) : null}

          {order.status_events && order.status_events.length > 0 ? (
            <Card title="Timeline">
              <ul className="space-y-1 text-sm text-emerald-200/80">
                {order.status_events.map((event) => (
                  <li key={event.id}>
                    {event.to_status}{" "}
                    <span className="text-emerald-400/60">{event.created_at}</span>
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
