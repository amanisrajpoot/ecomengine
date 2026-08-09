"use client";

import { NotificationFeed } from "@commerce/ui";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { api, getToken } from "../../lib/session";

const NOTIFICATIONS_SEEN_KEY = "ce.customer.notifications.lastSeen";

export default function NotificationsPage() {
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  if (!getToken()) return null;

  return (
    <NotificationFeed
      className="text-emerald-50"
      title="Notifications"
      description="SMS updates for your orders — scoped to your account."
      storageKey={NOTIFICATIONS_SEEN_KEY}
      loadNotifications={() => api().listNotifications({ limit: 100 })}
      cardClassName="!border-emerald-200/10 !bg-emerald-950/25"
      emptyTitle="No notifications yet"
      emptyDescription="Place an order with your phone number to receive SMS status updates."
      orderHref={(notification) =>
        notification.order_id ? `/orders/${notification.order_id}` : undefined
      }
    />
  );
}
