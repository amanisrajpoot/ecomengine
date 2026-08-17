"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import type { Business, Order } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { StatTile, StatusBadge } from "@commerce/ui";

import { OrderQueueCard } from "@/components/OrderQueueCard";
import { getApiClient } from "@/lib/api";
import { orderNeedsMerchantAction } from "@/lib/orderHelpers";
import { session } from "@/lib/session";

export default function BusinessDashboardPage() {
  const params = useParams<{ businessId: string }>();
  const businessId = params.businessId;

  const [business, setBusiness] = useState<Business | null>(null);
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    session.setActiveBusinessId(businessId);
    async function load() {
      setLoading(true);
      try {
        const api = getApiClient();
        const [b, list] = await Promise.all([
          api.getBusiness(businessId),
          api.listOrders({ business_id: businessId }),
        ]);
        setBusiness(b);
        setOrders(list);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load store");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [businessId]);

  const stats = useMemo(() => {
    const actionNeeded = orders.filter((o) =>
      orderNeedsMerchantAction(o.state_machine_profile, o.status),
    ).length;
    const inKitchen = orders.filter((o) =>
      ["ACCEPTED", "PREPARING", "PICKING"].includes(o.status),
    ).length;
    const ready = orders.filter((o) => o.status === "READY").length;
    return { actionNeeded, inKitchen, ready, total: orders.length };
  }, [orders]);

  const urgentOrders = useMemo(
    () =>
      orders
        .filter((o) => orderNeedsMerchantAction(o.state_machine_profile, o.status))
        .slice(0, 3),
    [orders],
  );

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">{business?.name ?? "Store"}</h1>
        {business ? (
          <div className="mt-2 flex items-center gap-2">
            <StatusBadge status={business.status} />
            <span className="text-sm text-gray-500">{business.type}</span>
          </div>
        ) : null}
      </div>

      {loading ? <p className="text-sm text-gray-500">Loading…</p> : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <div className="grid grid-cols-2 gap-3">
        <StatTile label="Action needed" value={stats.actionNeeded} accent={stats.actionNeeded > 0} />
        <StatTile label="In kitchen" value={stats.inKitchen} />
        <StatTile label="Ready" value={stats.ready} />
        <StatTile label="All orders" value={stats.total} hint="Today & recent" />
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        <Link
          href={`/business/${businessId}/orders`}
          className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
        >
          <p className="font-semibold text-gray-900">Order queue</p>
          <p className="mt-1 text-sm text-gray-500">Accept and progress incoming orders</p>
        </Link>
        <Link
          href={`/business/${businessId}/catalog`}
          className="rounded-2xl border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
        >
          <p className="font-semibold text-gray-900">Menu</p>
          <p className="mt-1 text-sm text-gray-500">Products and variants</p>
        </Link>
      </div>

      {urgentOrders.length > 0 ? (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-gray-900">Needs attention</h2>
            <Link
              href={`/business/${businessId}/orders`}
              className="text-sm font-medium text-[var(--brand)]"
            >
              View all
            </Link>
          </div>
          <ul className="space-y-3">
            {urgentOrders.map((order) => (
              <li key={order.id}>
                <OrderQueueCard order={order} businessId={businessId} />
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
