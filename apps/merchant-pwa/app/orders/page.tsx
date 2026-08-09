"use client";

import { ApiError } from "@commerce/api-client";
import type { Business, Order } from "@commerce/types";
import { formatPaise } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { KITCHEN_STATUSES } from "../../lib/order-actions";
import { api, getBusinessId, getToken, setBusinessId } from "../../lib/session";

export default function OrdersPage() {
  const router = useRouter();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selected, setSelected] = useState<string | null>(getBusinessId());
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
        const biz = await api().listBusinesses({ status: "ACTIVE" });
        if (cancelled) return;
        setBusinesses(biz);
        const current = selected ?? biz[0]?.id ?? null;
        if (current && !selected) {
          setSelected(current);
          setBusinessId(current);
        }
        if (current) {
          const rows = await api().listOrders({ business_id: current });
          if (!cancelled) setOrders(rows);
        }
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
  }, [router, selected]);

  const kitchen = useMemo(
    () => orders.filter((o) => KITCHEN_STATUSES.includes(o.status as (typeof KITCHEN_STATUSES)[number])),
    [orders],
  );

  async function onBusinessChange(id: string) {
    setSelected(id);
    setBusinessId(id);
    setLoading(true);
    setError(null);
    try {
      const rows = await api().listOrders({ business_id: id });
      setOrders(rows);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load orders");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <p className="font-display text-4xl text-amber-50">Orders</p>
      <label className="mt-6 flex flex-col gap-1.5 text-sm text-amber-50/80">
        <span>Business</span>
        <select
          className="rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
          value={selected ?? ""}
          onChange={(e) => onBusinessChange(e.target.value)}
        >
          {businesses.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name} ({b.type})
            </option>
          ))}
        </select>
      </label>

      {loading ? <p className="mt-8 text-amber-100/50">Loading queue…</p> : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      <section className="mt-8">
        <h2 className="text-sm uppercase tracking-wide text-amber-200/50">
          Kitchen queue ({kitchen.length})
        </h2>
        <ul className="mt-3 flex flex-col gap-2">
          {kitchen.map((order) => {
            const total =
              typeof order.pricing_snapshot?.total_paise === "number"
                ? order.pricing_snapshot.total_paise
                : null;
            return (
              <li key={order.id}>
                <Link
                  href={`/orders/${order.id}`}
                  className="flex items-center justify-between rounded-2xl border border-amber-200/10 bg-amber-950/25 px-4 py-3 transition hover:border-amber-300/25"
                >
                  <div>
                    <p className="font-medium text-amber-50">{order.status}</p>
                    <p className="text-xs text-amber-100/50">
                      {order.state_machine_profile} · {order.items.length} items
                    </p>
                  </div>
                  <span className="text-sm text-amber-100/70">
                    {total != null ? formatPaise(total) : "—"}
                  </span>
                </Link>
              </li>
            );
          })}
        </ul>
        {!loading && kitchen.length === 0 ? (
          <p className="mt-4 text-sm text-amber-100/55">No active kitchen orders.</p>
        ) : null}
      </section>

      <section className="mt-10">
        <h2 className="text-sm uppercase tracking-wide text-amber-200/50">All recent</h2>
        <ul className="mt-3 flex flex-col gap-2">
          {orders.slice(0, 12).map((order) => (
            <li key={order.id}>
              <Link
                href={`/orders/${order.id}`}
                className="block rounded-xl px-2 py-1.5 text-sm text-amber-100/70 hover:text-amber-50"
              >
                {order.status} · {new Date(order.created_at).toLocaleString("en-IN")}
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
