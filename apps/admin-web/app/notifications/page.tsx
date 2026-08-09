"use client";

import { NotificationFeed } from "@commerce/ui";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, getTenantId, getToken } from "../../lib/session";

const NOTIFICATIONS_SEEN_KEY = "ce.admin.notifications.lastSeen";

export default function NotificationsPage() {
  const router = useRouter();
  const [orderFilter, setOrderFilter] = useState("");
  const [tenantReady, setTenantReady] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setTenantReady(Boolean(getTenantId()));
  }, [router]);

  const loadNotifications = useCallback(
    () =>
      api().listNotifications({
        order_id: orderFilter.trim() || undefined,
        limit: 100,
      }),
    [orderFilter],
  );

  if (!getToken()) return null;

  if (!tenantReady) {
    return (
      <main className="mx-auto max-w-5xl px-5 py-10 text-violet-50">
        <p className="font-display text-4xl">Notifications</p>
        <p className="mt-4 text-rose-300">Select a tenant on the Tenants page first.</p>
      </main>
    );
  }

  return (
    <NotificationFeed
      className="max-w-5xl text-violet-50"
      title="Notifications"
      description="SMS delivery log for the tenant — order lifecycle events from Phase 21."
      storageKey={NOTIFICATIONS_SEEN_KEY}
      loadNotifications={loadNotifications}
      emptyTitle="No notifications"
      emptyDescription="Place an order with a customer phone to see SMS mock deliveries."
      orderHref={(notification) =>
        notification.order_id ? `/orders/${notification.order_id}/debugger` : undefined
      }
      headerExtra={
        <label className="mt-6 flex max-w-md flex-col gap-1.5 text-sm text-violet-50/80">
          <span>Filter by order ID (optional)</span>
          <input
            type="text"
            className="rounded-xl border border-violet-200/15 bg-violet-950/40 px-3 py-2.5 text-violet-50 placeholder:text-violet-100/30"
            placeholder="UUID"
            value={orderFilter}
            onChange={(e) => setOrderFilter(e.target.value)}
          />
        </label>
      }
    />
  );
}
