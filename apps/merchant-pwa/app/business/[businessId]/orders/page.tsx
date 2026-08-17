"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import type { Order } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Card } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export default function BusinessOrdersPage() {
  const params = useParams<{ businessId: string }>();
  const businessId = params.businessId;

  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    session.setActiveBusinessId(businessId);
    async function load() {
      setLoading(true);
      try {
        const list = await getApiClient().listOrders({ business_id: businessId });
        setOrders(list);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load orders");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [businessId]);

  return (
    <div className="space-y-4">
      <Link href={`/business/${businessId}`} className="text-xs text-amber-300/70 hover:text-amber-100">
        ← Dashboard
      </Link>
      <h1 className="text-2xl font-semibold">Orders</h1>
      {loading ? <p className="text-sm text-amber-200/60">Loading…</p> : null}
      {error ? <p className="text-sm text-red-300">{error}</p> : null}

      <ul className="space-y-2">
        {orders.map((order) => (
          <li key={order.id}>
            <Link href={`/business/${businessId}/orders/${order.id}`}>
              <Card className="transition-colors hover:border-emerald-500/50">
                <div className="flex justify-between gap-3">
                  <div>
                    <p className="font-medium">{order.status}</p>
                    <p className="font-mono text-xs text-amber-300/60">{order.id.slice(0, 8)}…</p>
                    <p className="text-xs text-amber-200/60">{order.placed_at ?? order.created_at}</p>
                  </div>
                  <span className="text-xs text-amber-300/60">Open →</span>
                </div>
              </Card>
            </Link>
          </li>
        ))}
      </ul>

      {!loading && orders.length === 0 ? (
        <p className="text-sm text-amber-200/60">No orders for this store yet.</p>
      ) : null}
    </div>
  );
}
