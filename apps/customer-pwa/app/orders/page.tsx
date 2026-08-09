"use client";

import { ApiError } from "@commerce/api-client";
import type { Order } from "@commerce/types";
import { EmptyState, StatusBadge, formatPaise } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, getToken } from "../../lib/session";

export default function OrdersPage() {
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const rows = await api().listOrders({ mine: true });
        if (!cancelled) setOrders(rows);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load orders");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router]);

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <p className="font-display text-4xl text-emerald-50">My orders</p>
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      {!error && !loading && orders.length === 0 ? (
        <EmptyState
          className="mt-8 border-emerald-200/15"
          title="No orders yet"
          description="Your past and active orders will show up here."
        />
      ) : null}
      <ul className="mt-8 flex flex-col gap-3">
        {orders.map((order) => {
          const total =
            typeof order.pricing_snapshot?.total_paise === "number"
              ? order.pricing_snapshot.total_paise
              : null;
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
                <p className="mt-2 text-sm text-emerald-100/55">
                  {total != null ? formatPaise(total) : "—"} ·{" "}
                  {new Date(order.created_at).toLocaleString("en-IN")}
                </p>
              </Link>
            </li>
          );
        })}
      </ul>
    </main>
  );
}
