"use client";

import type { Order } from "@commerce/types";
import {
  EmptyState,
  ErrorState,
  LiveIndicator,
  SkeletonCard,
  StatusBadge,
  formatPaise,
  usePolling,
} from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { api, getToken } from "../../lib/session";

const TERMINAL = new Set(["DELIVERED", "CANCELLED", "FAILED", "REFUNDED"]);

function isActive(order: Order): boolean {
  return !TERMINAL.has(order.status);
}

export default function OrdersPage() {
  const router = useRouter();
  const [businessNames, setBusinessNames] = useState<Record<string, string>>({});
  const [initialLoad, setInitialLoad] = useState(true);
  const [stopPoll, setStopPoll] = useState(false);

  const fetchOrders = useCallback(() => api().listOrders({ mine: true }), []);

  const { data: polled, error, loading, refresh } = usePolling(fetchOrders, {
    intervalMs: 10000,
    immediate: true,
    enabled: Boolean(getToken()) && !stopPoll,
  });

  const orders = polled ?? [];
  const hasActive = useMemo(() => orders.some(isActive), [orders]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    if (!loading) setInitialLoad(false);
  }, [loading, router]);

  useEffect(() => {
    if (polled && polled.length > 0 && !polled.some(isActive)) {
      setStopPoll(true);
    }
  }, [polled]);

  useEffect(() => {
    const ids = [...new Set(orders.map((o) => o.business_id).filter(Boolean))] as string[];
    const missing = ids.filter((id) => !businessNames[id]);
    if (!missing.length) return;
    let cancelled = false;
    (async () => {
      const entries = await Promise.all(
        missing.map(async (id) => {
          try {
            const biz = await api().getBusiness(id);
            return [id, biz.name] as const;
          } catch {
            return [id, "Store"] as const;
          }
        }),
      );
      if (!cancelled) {
        setBusinessNames((prev) => ({
          ...prev,
          ...Object.fromEntries(entries),
        }));
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [orders, businessNames]);

  const activeOrders = orders.filter(isActive);
  const pastOrders = orders.filter((o) => !isActive(o));

  function renderOrder(order: Order) {
    const total =
      typeof order.pricing_snapshot?.total_paise === "number"
        ? order.pricing_snapshot.total_paise
        : null;
    const storeName = order.business_id ? businessNames[order.business_id] : null;
    return (
      <li key={order.id}>
        <Link
          href={`/orders/${order.id}`}
          className="block rounded-2xl border border-emerald-200/10 px-5 py-4 transition hover:border-emerald-300/25"
        >
          <div className="flex items-center justify-between gap-3">
            <StatusBadge status={order.status} />
            <span className="text-xs uppercase tracking-wide text-emerald-200/50">
              {order.state_machine_profile}
            </span>
          </div>
          {storeName ? (
            <p className="mt-2 text-sm font-medium text-emerald-50/90">{storeName}</p>
          ) : null}
          <p className="mt-1 text-sm text-emerald-100/55">
            {total != null ? formatPaise(total) : "—"} ·{" "}
            {new Date(order.created_at).toLocaleString("en-IN")}
          </p>
        </Link>
      </li>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <div className="flex items-center justify-between gap-3">
        <p className="font-display text-4xl text-emerald-50">My orders</p>
        {hasActive ? <LiveIndicator /> : null}
      </div>

      {initialLoad && loading ? (
        <ul className="mt-8 flex flex-col gap-3">
          <SkeletonCard className="!border-emerald-200/10 !bg-emerald-950/20" />
          <SkeletonCard className="!border-emerald-200/10 !bg-emerald-950/20" />
        </ul>
      ) : null}

      {error && !orders.length ? (
        <ErrorState
          className="mt-8 border-emerald-200/15"
          message={error}
          onRetry={() => void refresh()}
        />
      ) : null}

      {!initialLoad && !error && orders.length === 0 ? (
        <EmptyState
          className="mt-8 border-emerald-200/15"
          title="No orders yet"
          description="Your past and active orders will show up here."
        />
      ) : null}

      {activeOrders.length ? (
        <section className="mt-8">
          <h2 className="text-sm uppercase tracking-wide text-emerald-200/50">Active</h2>
          <ul className="mt-3 flex flex-col gap-3">{activeOrders.map(renderOrder)}</ul>
        </section>
      ) : null}

      {pastOrders.length ? (
        <section className={activeOrders.length ? "mt-10" : "mt-8"}>
          <h2 className="text-sm uppercase tracking-wide text-emerald-200/50">Past</h2>
          <ul className="mt-3 flex flex-col gap-3">{pastOrders.map(renderOrder)}</ul>
        </section>
      ) : null}

      {error && orders.length ? (
        <p className="mt-4 text-sm text-rose-300/80">Could not refresh: {error}</p>
      ) : null}
    </main>
  );
}
