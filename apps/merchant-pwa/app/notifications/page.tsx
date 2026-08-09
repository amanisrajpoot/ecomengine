"use client";

import { NotificationFeed } from "@commerce/ui";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { api, getToken } from "../../lib/session";

const NOTIFICATIONS_SEEN_KEY = "ce.merchant.notifications.lastSeen";

export default function NotificationsPage() {
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  if (!getToken()) return null;

  return (
    <NotificationFeed
      className="text-amber-50"
      title="Notifications"
      description="SMS delivery log for your business tenant."
      storageKey={NOTIFICATIONS_SEEN_KEY}
      loadNotifications={() => api().listNotifications({ limit: 100 })}
      cardClassName="!border-amber-200/10 !bg-amber-950/25"
      emptyTitle="No notifications yet"
      emptyDescription="New order and status SMS events will appear here."
      orderHref={(notification) =>
        notification.order_id ? `/orders/${notification.order_id}` : undefined
      }
    />
  );
}
