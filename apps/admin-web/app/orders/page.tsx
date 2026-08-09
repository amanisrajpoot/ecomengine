"use client";

import { ApiError } from "@commerce/api-client";
import type { Order } from "@commerce/types";
import { formatPaise } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, getTenantId, getToken } from "../../lib/session";

export default function OrdersPage() {
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [status, setStatus] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    if (!getTenantId()) {
      setError("Set a tenant ID on login or pick one from Tenants.");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const rows = await api().listOrders(status ? { status } : undefined);
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
  }, [router, status]);

  return (
    <main className="mx-auto max-w-5xl px-5 py-10">
      <p className="font-display text-4xl text-violet-50">Orders</p>
      <label className="mt-6 flex flex-col gap-1.5 text-sm text-violet-50/80">
        <span>Filter by status</span>
        <select
          className="max-w-xs rounded-xl border border-violet-200/15 bg-violet-950/40 px-3 py-2.5 text-violet-50"
          value={status}
          onChange={(e) => setStatus(e.target.value)}
        >
          <option value="">All</option>
          {[
            "PAYMENT_CONFIRMED",
            "ACCEPTED",
            "PREPARING",
            "PICKING",
            "READY",
            "DELIVERED",
            "CANCELLED",
          ].map((s) => (
            <option key={s} value={s}>
              {s}
            </option>
          ))}
        </select>
      </label>
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      <ul className="mt-8 flex flex-col gap-2">
        {orders.map((order) => {
          const total =
            typeof order.pricing_snapshot?.total_paise === "number"
              ? order.pricing_snapshot.total_paise
              : null;
          return (
            <li key={order.id}>
              <Link
                href={`/orders/${order.id}/debugger`}
                className="flex items-center justify-between rounded-2xl border border-violet-200/10 px-5 py-4 transition hover:border-violet-300/25 hover:bg-violet-950/20"
              >
                <div>
                  <p className="font-medium text-violet-50">{order.status}</p>
                  <p className="text-xs text-violet-100/50">
                    {order.state_machine_profile} · {order.id.slice(0, 8)}…
                  </p>
                </div>
                <div className="text-right text-sm">
                  <p className="text-violet-100/80">
                    {total != null ? formatPaise(total) : "—"}
                  </p>
                  <p className="text-xs text-violet-300/70">Open debugger →</p>
                </div>
              </Link>
            </li>
          );
        })}
      </ul>
      {!error && orders.length === 0 ? (
        <p className="mt-8 text-sm text-violet-100/55">No orders in this tenant.</p>
      ) : null}
    </main>
  );
}
