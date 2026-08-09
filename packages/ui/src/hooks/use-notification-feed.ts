"use client";

import type { Notification } from "@commerce/types";
import { useCallback, useEffect, useMemo, useState } from "react";

import { usePolling } from "./use-polling";

function readLastSeen(storageKey: string): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(storageKey);
}

function writeLastSeen(storageKey: string, iso: string) {
  if (typeof window === "undefined") return;
  localStorage.setItem(storageKey, iso);
}

export function countUnreadNotifications(
  notifications: Notification[],
  lastSeen: string | null,
): number {
  if (!lastSeen) return notifications.length;
  const seenAt = new Date(lastSeen).getTime();
  return notifications.filter((row) => new Date(row.created_at).getTime() > seenAt).length;
}

export type UseNotificationFeedOptions = {
  pollIntervalMs?: number;
  enabled?: boolean;
  markSeenOnMount?: boolean;
};

export function useNotificationFeed(
  loadNotifications: () => Promise<Notification[]>,
  storageKey: string,
  options: UseNotificationFeedOptions = {},
) {
  const { pollIntervalMs = 15000, enabled = true, markSeenOnMount = false } = options;
  const [lastSeen, setLastSeen] = useState<string | null>(null);

  useEffect(() => {
    setLastSeen(readLastSeen(storageKey));
  }, [storageKey]);

  const fetcher = useCallback(() => loadNotifications(), [loadNotifications]);

  const { data, error, loading, refresh } = usePolling(fetcher, {
    intervalMs: pollIntervalMs,
    enabled,
  });

  const notifications = data ?? [];

  const unreadCount = useMemo(
    () => countUnreadNotifications(notifications, lastSeen),
    [notifications, lastSeen],
  );

  const markSeen = useCallback(() => {
    const now = new Date().toISOString();
    writeLastSeen(storageKey, now);
    setLastSeen(now);
  }, [storageKey]);

  useEffect(() => {
    if (markSeenOnMount) markSeen();
  }, [markSeenOnMount, markSeen]);

  return { notifications, unreadCount, error, loading, refresh, markSeen, lastSeen };
}
