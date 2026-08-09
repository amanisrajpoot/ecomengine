"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api, getTenantId, getToken } from "../lib/session";

type DashboardStats = {
  tenants: number;
  orders: number;
  activeOrders: number;
};

export default function HomePage() {
  const [meta, setMeta] = useState<{ name: string; version: string; environment: string } | null>(
    null,
  );
  const [stats, setStats] = useState<DashboardStats | null>(null);

  useEffect(() => {
    if (!getToken()) return;
    api()
      .getMeta()
      .then(setMeta)
      .catch(() => setMeta(null));
  }, []);

  useEffect(() => {
    if (!getToken()) return;
    let cancelled = false;
    (async () => {
      try {
        const tenants = await api().listTenants();
        let orders: Awaited<ReturnType<ReturnType<typeof api>["listOrders"]>> = [];
        if (getTenantId()) {
          orders = await api().listOrders();
        }
        if (cancelled) return;
        const active = orders.filter(
          (o) => !["DELIVERED", "CANCELLED", "FAILED", "REFUNDED"].includes(o.status),
        );
        setStats({
          tenants: tenants.length,
          orders: orders.length,
          activeOrders: active.length,
        });
      } catch {
        if (!cancelled) setStats(null);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  return (
    <main className="mx-auto max-w-4xl px-5 py-16">
      <p className="animate-rise font-display text-5xl text-violet-50 sm:text-6xl">Admin</p>
      <h1 className="animate-rise-delay mt-4 text-2xl font-medium text-violet-50/90">
        Platform ops & order debugger
      </h1>
      <p className="mt-4 max-w-lg text-violet-100/60">
        Trace the full chain — Order → Payment → Ledger → Fulfillment → Delivery → Settlement —
        across Food, Hyperlocal, and Courier verticals.
      </p>
      {meta ? (
        <p className="mt-4 text-sm text-violet-200/50">
          API {meta.name} v{meta.version} · {meta.environment}
        </p>
      ) : null}

      {stats ? (
        <div className="mt-8 grid gap-3 sm:grid-cols-3">
          {[
            { label: "Tenants", value: stats.tenants },
            { label: "Orders (tenant)", value: stats.orders },
            { label: "Active orders", value: stats.activeOrders },
          ].map((card) => (
            <div
              key={card.label}
              className="rounded-2xl border border-violet-200/10 bg-violet-950/25 px-5 py-4"
            >
              <p className="text-xs uppercase tracking-wide text-violet-200/50">{card.label}</p>
              <p className="mt-1 font-display text-3xl text-violet-50">{card.value}</p>
            </div>
          ))}
        </div>
      ) : getToken() && !getTenantId() ? (
        <p className="mt-6 text-sm text-amber-200/70">
          Pick a tenant from Tenants to load order counts on this dashboard.
        </p>
      ) : null}

      <div className="animate-rise-delay mt-8 flex flex-wrap gap-3">
        <Link
          href="/orders"
          className="rounded-xl bg-violet-500 px-5 py-3 text-sm font-semibold text-violet-50 hover:bg-violet-400"
        >
          Browse orders
        </Link>
        <Link
          href="/tenants"
          className="rounded-xl border border-violet-200/20 px-5 py-3 text-sm font-medium text-violet-50/90 hover:bg-white/5"
        >
          Tenants
        </Link>
        <Link
          href="/login"
          className="rounded-xl border border-violet-200/20 px-5 py-3 text-sm font-medium text-violet-50/90 hover:bg-white/5"
        >
          Sign in
        </Link>
      </div>
    </main>
  );
}
