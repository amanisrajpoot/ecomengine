"use client";

import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import type { Order } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { CategoryChip, EmptyState, Skeleton } from "@commerce/ui";

import { OrderQueueCard } from "@/components/OrderQueueCard";
import { getApiClient } from "@/lib/api";
import { orderNeedsMerchantAction } from "@/lib/orderHelpers";
import { session } from "@/lib/session";

type Filter = "ACTION" | "ALL";

export default function BusinessOrdersPage() {
  const params = useParams<{ businessId: string }>();
  const businessId = params.businessId;

  const [orders, setOrders] = useState<Order[]>([]);
  const [filter, setFilter] = useState<Filter>("ACTION");
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

  const filtered = useMemo(() => {
    if (filter === "ALL") return orders;
    return orders.filter((o) => orderNeedsMerchantAction(o.state_machine_profile, o.status));
  }, [orders, filter]);

  const actionCount = useMemo(
    () =>
      orders.filter((o) => orderNeedsMerchantAction(o.state_machine_profile, o.status)).length,
    [orders],
  );

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Orders</h1>
        <p className="text-sm text-gray-500">Kitchen display queue for this store.</p>
      </div>

      <div className="flex gap-2">
        <CategoryChip
          label={`Action needed (${actionCount})`}
          active={filter === "ACTION"}
          onClick={() => setFilter("ACTION")}
        />
        <CategoryChip label="All orders" active={filter === "ALL"} onClick={() => setFilter("ALL")} />
      </div>

      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
      ) : null}

      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <ul className="space-y-3">
        {filtered.map((order) => (
          <li key={order.id}>
            <OrderQueueCard order={order} businessId={businessId} />
          </li>
        ))}
      </ul>

      {!loading && filtered.length === 0 ? (
        <EmptyState
          title={filter === "ACTION" ? "No orders need action" : "No orders yet"}
          description={
            filter === "ACTION"
              ? "New orders will appear here when customers place them."
              : "Orders for this store will show up here."
          }
        />
      ) : null}
    </div>
  );
}
