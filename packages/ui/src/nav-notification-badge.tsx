"use client";

import type { Notification } from "@commerce/types";
import { useCallback } from "react";

import { Badge } from "./badge";
import { useNotificationFeed } from "./hooks/use-notification-feed";

type NavNotificationBadgeProps = {
  loadNotifications: () => Promise<Notification[]>;
  storageKey: string;
  enabled?: boolean;
  pollIntervalMs?: number;
  className?: string;
};

export function NavNotificationBadge({
  loadNotifications,
  storageKey,
  enabled = true,
  pollIntervalMs = 15000,
  className = "",
}: NavNotificationBadgeProps) {
  const fetcher = useCallback(() => loadNotifications(), [loadNotifications]);
  const { unreadCount } = useNotificationFeed(fetcher, storageKey, {
    enabled,
    pollIntervalMs,
    markSeenOnMount: false,
  });
  return <Badge count={unreadCount} className={className} />;
}
