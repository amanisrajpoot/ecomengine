"use client";

import { ApiError } from "@commerce/api-client";
import type { Order } from "@commerce/types";
import {
  OrderStatusStepper,
  PriceBreakdown,
  Spinner,
  StatusBadge,
  formatPaise,
} from "@commerce/ui";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, getToken } from "../../../lib/session";

const TERMINAL = new Set(["DELIVERED", "CANCELLED", "FAILED", "REFUNDED"]);

export default function OrderDetailPage() {
  const router = useRouter();
  const params = useParams<{ orderId: string }>();
  const [order, setOrder] = useState<Order | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const data = await api().getOrder(params.orderId);
    setOrder(data);
    return data;
  }, [params.orderId]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        await load();
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Order not found");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [load, router]);

  useEffect(() => {
    if (!order || TERMINAL.has(order.status)) return;
    const timer = window.setInterval(() => {
      load().catch(() => undefined);
    }, 5000);
    return () => window.clearInterval(timer);
  }, [load, order?.status]);

  if (loading) {
    return (
      <main className="mx-auto flex max-w-xl justify-center px-5 py-20">
        <Spinner size="lg" className="text-emerald-300" />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-xl px-5 py-10">
      <p className="font-display text-4xl text-emerald-50">Order</p>
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      {order ? (
        <div className="mt-8 space-y-5">
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={order.status} />
            <p className="text-sm text-emerald-100/55">
              {order.state_machine_profile} · {order.fulfillment_type} · {order.payment_method}
            </p>
          </div>

          <OrderStatusStepper profile={order.state_machine_profile} status={order.status} />

          <PriceBreakdown snapshot={order.pricing_snapshot} />

          <ul className="divide-y divide-emerald-200/10 rounded-2xl border border-emerald-200/10">
            {order.items.map((item) => (
              <li key={item.id} className="flex justify-between px-4 py-3 text-sm">
                <span className="text-emerald-50">
                  {item.name_snapshot} × {item.quantity}
                </span>
                <span className="text-emerald-100/60">
                  {formatPaise(item.unit_price_paise * item.quantity)}
                </span>
              </li>
            ))}
          </ul>

          {!TERMINAL.has(order.status) ? (
            <p className="text-xs text-emerald-100/40">Status refreshes every 5 seconds.</p>
          ) : null}
        </div>
      ) : null}
    </main>
  );
}
