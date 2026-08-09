"use client";

import { ApiError } from "@commerce/api-client";
import type { Notification } from "@commerce/types";
import { NotificationCard, Spinner } from "@commerce/ui";
import { useCallback, useEffect, useState } from "react";

type OrderNotificationsPanelProps = {
  orderId: string;
  loadNotifications: (orderId: string) => Promise<Notification[]>;
  className?: string;
  emptyMessage?: string;
};

export function OrderNotificationsPanel({
  orderId,
  loadNotifications,
  className = "",
  emptyMessage = "No SMS notifications for this order yet.",
}: OrderNotificationsPanelProps) {
  const [rows, setRows] = useState<Notification[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const data = await loadNotifications(orderId);
    setRows(data);
    return data;
  }, [loadNotifications, orderId]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await load();
        if (!cancelled) setError(null);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Could not load notifications");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [load]);

  return (
    <section
      className={`rounded-2xl border border-white/10 bg-black/20 px-4 py-4 ${className}`}
    >
      <p className="text-sm font-medium text-white/80">Notifications</p>
      {loading ? (
        <div className="mt-4 flex justify-center">
          <Spinner size="sm" />
        </div>
      ) : rows.length === 0 ? (
        <p className="mt-3 text-sm text-white/45">{emptyMessage}</p>
      ) : (
        <ul className="mt-3 flex flex-col gap-2">
          {rows.map((notification) => (
            <li key={notification.id}>
              <NotificationCard
                notification={notification}
                className="!border-white/5 !bg-black/10"
              />
            </li>
          ))}
        </ul>
      )}
      {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
    </section>
  );
}
