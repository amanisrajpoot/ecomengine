"use client";

import { ApiError } from "@commerce/api-client";
import type { Business, Order } from "@commerce/types";
import {
  Button,
  ErrorState,
  LiveIndicator,
  OrderNotificationsPanel,
  OrderStatusStepper,
  OrderStatusTimeline,
  OrderTrackingPanel,
  PaymentPanel,
  PriceBreakdown,
  SkeletonCard,
  Spinner,
  StatusBadge,
  formatPaise,
  usePolling,
} from "@commerce/ui";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, getToken } from "../../../lib/session";

const TERMINAL = new Set(["DELIVERED", "CANCELLED", "FAILED", "REFUNDED"]);
const CUSTOMER_CANCELLABLE = new Set(["PAYMENT_PENDING", "PAYMENT_CONFIRMED", "ACCEPTED"]);

export default function OrderDetailPage() {
  const router = useRouter();
  const params = useParams<{ orderId: string }>();
  const [business, setBusiness] = useState<Business | null>(null);
  const [busy, setBusy] = useState(false);
  const [actionError, setActionError] = useState<string | null>(null);
  const [stopPoll, setStopPoll] = useState(false);

  const fetchOrder = useCallback(
    () => api().getOrder(params.orderId),
    [params.orderId],
  );

  const { data: order, error, loading, refresh } = usePolling(fetchOrder, {
    intervalMs: 5000,
    enabled: Boolean(getToken()) && !stopPoll,
    immediate: true,
  });

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
    }
  }, [router]);

  useEffect(() => {
    if (order && TERMINAL.has(order.status)) {
      setStopPoll(true);
    }
  }, [order?.status]);

  useEffect(() => {
    if (!order?.business_id) return;
    let cancelled = false;
    (async () => {
      try {
        const biz = await api().getBusiness(order.business_id!);
        if (!cancelled) setBusiness(biz);
      } catch {
        if (!cancelled) setBusiness(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [order?.business_id]);

  async function cancelOrder() {
    if (!order) return;
    setBusy(true);
    setActionError(null);
    try {
      await api().transitionOrder(order.id, {
        to_status: "CANCELLED",
        actor: "customer",
        reason: "Cancelled by customer",
      });
      await refresh();
    } catch (err) {
      setActionError(err instanceof ApiError ? err.message : "Could not cancel order");
    } finally {
      setBusy(false);
    }
  }

  if (loading && !order) {
    return (
      <main className="mx-auto max-w-xl px-5 py-10">
        <Spinner size="lg" className="mx-auto mt-12 text-emerald-300" />
      </main>
    );
  }

  if (error && !order) {
    return (
      <main className="mx-auto max-w-xl px-5 py-10">
        <Link href="/orders" className="text-sm text-emerald-100/50 hover:text-emerald-50">
          ← My orders
        </Link>
        <ErrorState
          className="mt-8 border-emerald-200/15"
          message={error}
          onRetry={() => void refresh()}
        />
      </main>
    );
  }

  const canCancel = order && CUSTOMER_CANCELLABLE.has(order.status);
  const isLive = order && !TERMINAL.has(order.status);

  return (
    <main className="mx-auto max-w-xl px-5 py-10">
      <Link href="/orders" className="text-sm text-emerald-100/50 hover:text-emerald-50">
        ← My orders
      </Link>
      <div className="mt-4 flex items-center justify-between gap-3">
        <p className="font-display text-4xl text-emerald-50">Order</p>
        {isLive ? <LiveIndicator /> : null}
      </div>
      {business ? (
        <p className="mt-2 text-sm text-emerald-100/55">{business.name}</p>
      ) : order?.business_id ? (
        <SkeletonCard className="mt-2 !border-emerald-200/10 !bg-emerald-950/20 !p-3" />
      ) : null}
      {actionError ? <p className="mt-4 text-rose-300">{actionError}</p> : null}
      {order ? (
        <div className="mt-8 space-y-5">
          <div className="flex flex-wrap items-center gap-3">
            <StatusBadge status={order.status} />
            <p className="text-sm text-emerald-100/55">
              {order.state_machine_profile} · {order.fulfillment_type} · {order.payment_method}
            </p>
          </div>

          <OrderStatusStepper profile={order.state_machine_profile} status={order.status} />

          <PaymentPanel
            order={order}
            api={api()}
            onUpdate={() => {
              refresh().catch(() => undefined);
            }}
          />

          <OrderTrackingPanel order={order} api={api()} />

          <OrderNotificationsPanel
            orderId={order.id}
            loadNotifications={(orderId) => api().listNotifications({ order_id: orderId })}
          />

          {order.status_events?.length ? (
            <OrderStatusTimeline
              events={order.status_events}
              className="!border-emerald-200/10 !bg-emerald-950/25"
            />
          ) : null}

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

          {canCancel ? (
            <Button
              type="button"
              variant="ghost"
              className="w-full text-rose-300 hover:bg-rose-500/10"
              disabled={busy}
              onClick={() => void cancelOrder()}
            >
              {busy ? "Cancelling…" : "Cancel order"}
            </Button>
          ) : null}
        </div>
      ) : null}
    </main>
  );
}
