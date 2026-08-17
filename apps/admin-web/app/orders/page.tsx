"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { Order } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Card, Input } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export default function OrdersPage() {
  const [orders, setOrders] = useState<Order[]>([]);
  const [statusFilter, setStatusFilter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        if (!session.getAccessToken()) {
          setError("Sign in first.");
          return;
        }
        const list = await getApiClient().listOrders(
          statusFilter ? { status: statusFilter } : undefined,
        );
        setOrders(list);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load orders");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [statusFilter]);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Orders</h1>
      <p className="text-sm text-violet-200/70">
        Open any order for the full debugger trace. Tenant context required for tenant-scoped lists.
      </p>
      <Input
        label="Filter by status"
        value={statusFilter}
        onChange={(e) => setStatusFilter(e.target.value)}
        placeholder="e.g. PAYMENT_CONFIRMED"
      />
      {loading ? <p className="text-sm text-violet-200/60">Loading…</p> : null}
      {error ? (
        <p className="text-sm text-red-300">
          {error}{" "}
          <Link href="/settings" className="underline">Settings</Link>
        </p>
      ) : null}

      <ul className="space-y-2">
        {orders.map((order) => (
          <li key={order.id}>
            <Link href={`/orders/${order.id}`}>
              <Card className="transition-colors hover:border-emerald-500/50">
                <div className="flex justify-between gap-3">
                  <div>
                    <p className="font-medium">{order.status}</p>
                    <p className="font-mono text-xs text-violet-300/60">{order.id}</p>
                    <p className="text-xs text-violet-200/60">{order.state_machine_profile}</p>
                  </div>
                  <span className="text-xs text-violet-300/60">Debug →</span>
                </div>
              </Card>
            </Link>
          </li>
        ))}
      </ul>

      {!loading && !error && orders.length === 0 ? (
        <p className="text-sm text-violet-200/60">No orders in this tenant.</p>
      ) : null}
    </div>
  );
}
