"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { Order } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Card } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        if (!session.getAccessToken()) {
          setError("Sign in to view orders.");
          return;
        }
        const list = await getApiClient().listOrders();
        setOrders(list);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load orders");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Orders</h1>
        <p className="text-sm text-emerald-200/70">Your order history in this tenant.</p>
      </div>

      {loading ? <p className="text-sm text-emerald-200/60">Loading…</p> : null}
      {error ? (
        <p className="text-sm text-red-300">
          {error}{" "}
          <Link href="/login" className="underline">Sign in</Link>
        </p>
      ) : null}

      <ul className="space-y-2">
        {orders.map((order) => (
          <li key={order.id}>
            <Link href={`/orders/${order.id}`}>
              <Card className="transition-colors hover:border-emerald-500/50">
                <div className="flex items-center justify-between gap-3">
                  <div>
                    <p className="font-mono text-xs text-emerald-300/70">{order.id.slice(0, 8)}…</p>
                    <p className="font-medium">{order.status}</p>
                    <p className="text-xs text-emerald-200/60">
                      {order.placed_at ?? order.created_at}
                    </p>
                  </div>
                  <span className="text-xs text-emerald-300/60">Details →</span>
                </div>
              </Card>
            </Link>
          </li>
        ))}
      </ul>

      {!loading && !error && orders.length === 0 ? (
        <p className="text-sm text-emerald-200/60">No orders yet.</p>
      ) : null}
    </div>
  );
}
