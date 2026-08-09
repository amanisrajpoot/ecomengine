"use client";

import type { Notification } from "@commerce/types";

import { EmptyState } from "./empty-state";
import { ErrorState } from "./error-state";
import { useNotificationFeed } from "./hooks/use-notification-feed";
import { LiveIndicator } from "./live-indicator";
import { NotificationCard } from "./notification-card";
import { SkeletonCard } from "./skeleton";
import { Spinner } from "./spinner";

export type NotificationFeedProps = {
  loadNotifications: () => Promise<Notification[]>;
  storageKey: string;
  pollIntervalMs?: number;
  enabled?: boolean;
  markSeenOnMount?: boolean;
  title?: string;
  description?: string;
  cardClassName?: string;
  emptyTitle?: string;
  emptyDescription?: string;
  orderHref?: (notification: Notification) => string | undefined;
  headerExtra?: React.ReactNode;
  className?: string;
};

export function NotificationFeed({
  loadNotifications,
  storageKey,
  pollIntervalMs = 10000,
  enabled = true,
  markSeenOnMount = true,
  title = "Notifications",
  description,
  cardClassName = "",
  emptyTitle = "No notifications yet",
  emptyDescription = "Updates will appear here when events are sent.",
  orderHref,
  headerExtra,
  className = "",
}: NotificationFeedProps) {
  const { notifications, error, loading, refresh } = useNotificationFeed(
    loadNotifications,
    storageKey,
    { pollIntervalMs, enabled, markSeenOnMount },
  );

  return (
    <main className={`mx-auto max-w-xl px-5 py-10 ${className}`}>
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="font-display text-4xl text-inherit">{title}</p>
          {description ? <p className="mt-2 text-sm opacity-60">{description}</p> : null}
        </div>
        {enabled ? <LiveIndicator /> : null}
      </div>

      {headerExtra}

      {loading && notifications.length === 0 ? (
        <div className="mt-8 flex flex-col gap-3">
          <SkeletonCard />
          <SkeletonCard />
        </div>
      ) : null}

      {error ? (
        <ErrorState
          className="mt-8"
          message={error}
          onRetry={() => {
            refresh().catch(() => undefined);
          }}
        />
      ) : null}

      <ul className="mt-8 flex flex-col gap-3">
        {notifications.map((notification) => (
          <li key={notification.id}>
            <NotificationCard
              notification={notification}
              className={cardClassName}
              orderHref={orderHref?.(notification)}
            />
          </li>
        ))}
      </ul>

      {!loading && !error && notifications.length === 0 ? (
        <EmptyState
          className="mt-8 border-white/10"
          title={emptyTitle}
          description={emptyDescription}
        />
      ) : null}

      {loading && notifications.length > 0 ? (
        <div className="mt-4 flex justify-center">
          <Spinner size="sm" label="Refreshing" />
        </div>
      ) : null}
    </main>
  );
}
