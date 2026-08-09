"use client";

import { ApiError } from "@commerce/api-client";
import type { Notification } from "@commerce/types";
import { EmptyState, NotificationCard, Spinner } from "@commerce/ui";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, getTenantId, getToken } from "../../lib/session";

export default function NotificationsPage() {
  const router = useRouter();
  const [rows, setRows] = useState<Notification[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [orderFilter, setOrderFilter] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    if (!getTenantId()) {
      setError("Select a tenant on the Tenants page first.");
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await api().listNotifications({
          order_id: orderFilter.trim() || undefined,
          limit: 100,
        });
        if (!cancelled) setRows(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load notifications");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [orderFilter, router]);

  return (
    <main className="mx-auto max-w-5xl px-5 py-10">
      <p className="font-display text-4xl text-violet-50">Notifications</p>
      <p className="mt-2 text-sm text-violet-100/55">
        SMS delivery log for the tenant — order lifecycle events from Phase 21.
      </p>

      <label className="mt-6 flex max-w-md flex-col gap-1.5 text-sm text-violet-50/80">
        <span>Filter by order ID (optional)</span>
        <input
          type="text"
          className="rounded-xl border border-violet-200/15 bg-violet-950/40 px-3 py-2.5 text-violet-50 placeholder:text-violet-100/30"
          placeholder="UUID"
          value={orderFilter}
          onChange={(e) => {
            setLoading(true);
            setOrderFilter(e.target.value);
          }}
        />
      </label>

      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-violet-300" />
        </div>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      <ul className="mt-8 flex flex-col gap-3">
        {rows.map((notification) => (
          <li key={notification.id}>
            <NotificationCard notification={notification} />
          </li>
        ))}
      </ul>

      {!loading && !error && rows.length === 0 ? (
        <EmptyState
          className="mt-8 border-violet-200/15"
          title="No notifications"
          description="Place an order with a customer phone to see SMS mock deliveries."
        />
      ) : null}
    </main>
  );
}
