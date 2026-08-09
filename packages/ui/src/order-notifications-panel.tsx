"use client";

import type { Notification } from "@commerce/types";
import { useCallback } from "react";

import { ErrorState } from "./error-state";
import { usePolling } from "./hooks/use-polling";
import { LiveIndicator } from "./live-indicator";
import { NotificationCard } from "./notification-card";
import { Spinner } from "./spinner";

type OrderNotificationsPanelProps = {
  orderId: string;
  loadNotifications: (orderId: string) => Promise<Notification[]>;
  className?: string;
  emptyMessage?: string;
  pollIntervalMs?: number;
};

export function OrderNotificationsPanel({
  orderId,
  loadNotifications,
  className = "",
  emptyMessage = "No SMS notifications for this order yet.",
  pollIntervalMs = 5000,
}: OrderNotificationsPanelProps) {
  const fetcher = useCallback(
    () => loadNotifications(orderId),
    [loadNotifications, orderId],
  );

  const { data, error, loading, refresh } = usePolling(fetcher, {
    intervalMs: pollIntervalMs,
    immediate: true,
  });

  const rows = data ?? [];
  const message = error
    ? error
    : null;

  return (
    <section
      className={`rounded-2xl border border-white/10 bg-black/20 px-4 py-4 ${className}`}
    >
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-medium text-white/80">Notifications</p>
        <LiveIndicator label={`${pollIntervalMs / 1000}s`} />
      </div>
      {loading && rows.length === 0 ? (
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
      {message ? (
        <ErrorState
          className="mt-3 !border-rose-400/15 !bg-rose-950/10 !py-4"
          title="Could not load"
          message={message}
          onRetry={() => {
            refresh().catch(() => undefined);
          }}
        />
      ) : null}
    </section>
  );
}
