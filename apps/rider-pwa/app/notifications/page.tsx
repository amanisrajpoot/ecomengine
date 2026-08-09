"use client";

import { NotificationFeed } from "@commerce/ui";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { api, getToken } from "../../lib/session";

const NOTIFICATIONS_SEEN_KEY = "ce.rider.notifications.lastSeen";

export default function RiderNotificationsPage() {
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  if (!getToken()) return null;

  return (
    <NotificationFeed
      className="text-sky-50"
      title="Alerts"
      description="SMS updates for deliveries assigned to you."
      storageKey={NOTIFICATIONS_SEEN_KEY}
      loadNotifications={() => api().listNotifications({ limit: 100 })}
      cardClassName="!border-sky-200/10 !bg-sky-950/25"
      emptyTitle="No alerts yet"
      emptyDescription="Accept a delivery job to receive status SMS notifications."
    />
  );
}
