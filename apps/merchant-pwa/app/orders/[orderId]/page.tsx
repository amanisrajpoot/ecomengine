"use client";

import { ApiError } from "@commerce/api-client";
import type { Fulfillment, Order } from "@commerce/types";
import { Button, formatPaise } from "@commerce/ui";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { merchantActionsFor } from "../../../lib/order-actions";
import { api, getToken } from "../../../lib/session";

export default function OrderDetailPage() {
  const router = useRouter();
  const params = useParams<{ orderId: string }>();
  const [order, setOrder] = useState<Order | null>(null);
  const [fulfillment, setFulfillment] = useState<Fulfillment | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const load = useCallback(async () => {
    const data = await api().getOrder(params.orderId);
    setOrder(data);
    try {
      const ful = await api().getOrderFulfillment(params.orderId);
      setFulfillment(ful);
    } catch {
      setFulfillment(null);
    }
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
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [load, router]);

  async function runAction(to_status: string, actor: string) {
    if (!order) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await api().transitionOrder(order.id, {
        to_status,
        actor,
        reason: "merchant_pwa",
      });
      setOrder(updated);
      try {
        const ful = await api().getOrderFulfillment(order.id);
        setFulfillment(ful);
      } catch {
        /* optional */
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Transition failed");
    } finally {
      setBusy(false);
    }
  }

  const total =
    typeof order?.pricing_snapshot?.total_paise === "number"
      ? order.pricing_snapshot.total_paise
      : null;
  const actions = order ? merchantActionsFor(order) : [];

  return (
    <main className="mx-auto max-w-xl px-5 py-10">
      <p className="font-display text-4xl text-amber-50">Order</p>
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      {order ? (
        <div className="mt-8 space-y-5">
          <div>
            <p className="text-2xl text-amber-50">{order.status}</p>
            <p className="text-sm text-amber-100/55">
              {order.state_machine_profile} · {order.payment_method}
            </p>
            <p className="mt-2 font-display text-3xl text-amber-50">
              {total != null ? formatPaise(total) : "—"}
            </p>
          </div>

          <ul className="divide-y divide-amber-200/10 rounded-2xl border border-amber-200/10">
            {order.items.map((item) => (
              <li key={item.id} className="flex justify-between px-4 py-3 text-sm">
                <span className="text-amber-50">
                  {item.name_snapshot} × {item.quantity}
                </span>
                <span className="text-amber-100/60">
                  {formatPaise(item.unit_price_paise * item.quantity)}
                </span>
              </li>
            ))}
          </ul>

          {fulfillment ? (
            <p className="text-sm text-amber-100/55">
              Fulfillment: {fulfillment.status} ({fulfillment.type})
            </p>
          ) : null}

          <div className="flex flex-col gap-2">
            {actions.map((action) => (
              <Button
                key={action.to_status}
                type="button"
                variant={action.variant === "danger" ? "ghost" : "primary"}
                className={
                  action.variant === "danger"
                    ? "border border-rose-400/30 text-rose-200 hover:bg-rose-950/40"
                    : "w-full bg-amber-500 text-amber-950 hover:bg-amber-400"
                }
                disabled={busy}
                onClick={() => runAction(action.to_status, action.actor)}
              >
                {action.label}
              </Button>
            ))}
          </div>

          {order.status_events?.length ? (
            <ul className="space-y-1 text-xs text-amber-100/45">
              {order.status_events.map((e, i) => (
                <li key={`${e.to_status}-${i}`}>
                  {e.from_status ?? "—"} → {e.to_status} ({e.actor_role})
                </li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}
    </main>
  );
}
