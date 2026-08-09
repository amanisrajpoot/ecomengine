"use client";

import { ApiError } from "@commerce/api-client";
import type { Business, Order } from "@commerce/types";
import {
  EmptyState,
  formatPaise,
  LiveIndicator,
  Spinner,
  StatusBadge,
  useToast,
} from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { KITCHEN_STATUSES } from "../../lib/order-actions";
import { api, getBusinessId, getToken, setBusinessId } from "../../lib/session";

const POLL_MS = 8000;

export default function OrdersPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selected, setSelected] = useState<string | null>(getBusinessId());
  const [orders, setOrders] = useState<Order[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const knownKitchenIdsRef = useRef<Set<string>>(new Set());
  const kitchenInitializedRef = useRef(false);

  const notifyNewKitchenOrders = useCallback(
    (rows: Order[]) => {
      const kitchen = rows.filter((order) =>
        KITCHEN_STATUSES.includes(order.status as (typeof KITCHEN_STATUSES)[number]),
      );
      if (!kitchenInitializedRef.current) {
        kitchen.forEach((order) => knownKitchenIdsRef.current.add(order.id));
        kitchenInitializedRef.current = true;
        return;
      }
      for (const order of kitchen) {
        if (knownKitchenIdsRef.current.has(order.id)) continue;
        knownKitchenIdsRef.current.add(order.id);
        if (order.status !== "PAYMENT_CONFIRMED") continue;
        const total =
          typeof order.pricing_snapshot?.total_paise === "number"
            ? order.pricing_snapshot.total_paise
            : null;
        const itemCount = order.items.reduce((sum, item) => sum + item.quantity, 0);
        toast({
          title: "New order",
          description: `${itemCount} item${itemCount === 1 ? "" : "s"}${total != null ? ` · ${formatPaise(total)}` : ""}`,
          variant: "success",
          durationMs: 8000,
        });
      }
    },
    [toast],
  );

  const loadOrders = useCallback(
    async (businessId: string) => {
      const rows = await api().listOrders({ business_id: businessId });
      setOrders(rows);
      notifyNewKitchenOrders(rows);
    },
    [notifyNewKitchenOrders],
  );

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
        if (current) await loadOrders(current);
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
  }, [loadOrders, router, selected]);

  useEffect(() => {
    if (!selected || loading) return;
    const timer = window.setInterval(() => {
      loadOrders(selected).catch(() => undefined);
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [loadOrders, loading, selected]);

  const kitchen = useMemo(
    () =>
      orders.filter((o) =>
        KITCHEN_STATUSES.includes(o.status as (typeof KITCHEN_STATUSES)[number]),
      ),
    [orders],
  );

  async function onBusinessChange(id: string) {
    knownKitchenIdsRef.current = new Set();
    kitchenInitializedRef.current = false;
    setSelected(id);
    setBusinessId(id);
    setLoading(true);
    setError(null);
    try {
      await loadOrders(id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load orders");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <p className="font-display text-4xl text-amber-50">Kitchen board</p>
        {!loading && selected ? <LiveIndicator label={`${POLL_MS / 1000}s`} /> : null}
      </div>
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

      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-amber-300" />
        </div>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      <section className="mt-8">
        <h2 className="text-sm uppercase tracking-wide text-amber-200/50">
          Active ({kitchen.length})
        </h2>
        {!loading && kitchen.length === 0 ? (
          <EmptyState
            className="mt-4 border-amber-200/15"
            title="No active kitchen orders"
            description="New paid orders will appear here automatically."
          />
        ) : (
          <ul className="mt-3 grid gap-3 sm:grid-cols-2">
            {kitchen.map((order) => {
              const total =
                typeof order.pricing_snapshot?.total_paise === "number"
                  ? order.pricing_snapshot.total_paise
                  : null;
              const itemCount = order.items.reduce((sum, item) => sum + item.quantity, 0);
              return (
                <li key={order.id}>
                  <Link
                    href={`/orders/${order.id}`}
                    className="flex h-full flex-col rounded-2xl border border-amber-200/10 bg-amber-950/25 px-4 py-4 transition hover:border-amber-300/25"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <StatusBadge status={order.status} />
                      <span className="text-sm font-medium text-amber-100/80">
                        {total != null ? formatPaise(total) : "—"}
                      </span>
                    </div>
                    <p className="mt-3 text-sm text-amber-50">
                      {itemCount} item{itemCount === 1 ? "" : "s"}
                    </p>
                    <p className="mt-1 text-xs text-amber-100/45">
                      {order.state_machine_profile} ·{" "}
                      {new Date(order.created_at).toLocaleTimeString("en-IN", {
                        hour: "2-digit",
                        minute: "2-digit",
                      })}
                    </p>
                  </Link>
                </li>
              );
            })}
          </ul>
        )}
      </section>

      <section className="mt-10">
        <h2 className="text-sm uppercase tracking-wide text-amber-200/50">All recent</h2>
        <ul className="mt-3 flex flex-col gap-2">
          {orders.slice(0, 12).map((order) => (
            <li key={order.id}>
              <Link
                href={`/orders/${order.id}`}
                className="flex items-center justify-between rounded-xl px-2 py-1.5 text-sm hover:bg-amber-950/20"
              >
                <span className="flex items-center gap-2 text-amber-100/70 hover:text-amber-50">
                  <StatusBadge status={order.status} className="!text-[10px]" />
                  {new Date(order.created_at).toLocaleString("en-IN")}
                </span>
              </Link>
            </li>
          ))}
        </ul>
      </section>
    </main>
  );
}
