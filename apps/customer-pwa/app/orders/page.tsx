"use client";

import { ApiError } from "@commerce/api-client";
import type { Order } from "@commerce/types";
import { formatPaise } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, getToken } from "../../lib/session";

export default function OrdersPage() {
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const rows = await api().listOrders();
        if (!cancelled) setOrders(rows);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load orders");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router]);

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <p className="font-display text-4xl text-emerald-50">Orders</p>
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
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
                <div className="flex items-baseline justify-between gap-3">
                  <p className="font-medium text-emerald-50">{order.status}</p>
                  <span className="text-xs uppercase tracking-wide text-emerald-200/50">
                    {order.state_machine_profile}
                  </span>
                </div>
                <p className="mt-1 text-sm text-emerald-100/55">
                  {total != null ? formatPaise(total) : "—"} ·{" "}
                  {new Date(order.created_at).toLocaleString("en-IN")}
                </p>
              </Link>
            </li>
          );
        })}
      </ul>
      {!error && orders.length === 0 ? (
        <p className="mt-8 text-emerald-100/55">No orders yet.</p>
      ) : null}
    </main>
  );
}
