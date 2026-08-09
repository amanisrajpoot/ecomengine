"use client";

import { ApiError } from "@commerce/api-client";
import type { Notification } from "@commerce/types";
import { EmptyState, NotificationCard, Spinner } from "@commerce/ui";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, getToken } from "../../lib/session";

export default function NotificationsPage() {
  const router = useRouter();
  const [rows, setRows] = useState<Notification[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await api().listNotifications({ limit: 100 });
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
  }, [router]);

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <p className="font-display text-4xl text-amber-50">Notifications</p>
      <p className="mt-2 text-sm text-amber-100/55">
        Tenant-wide SMS delivery log for order lifecycle events.
      </p>

      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-amber-300" />
        </div>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      <ul className="mt-8 flex flex-col gap-3">
        {rows.map((notification) => (
          <li key={notification.id}>
            <NotificationCard
              notification={notification}
              className="!border-amber-200/10 !bg-amber-950/25"
            />
          </li>
        ))}
      </ul>

      {!loading && !error && rows.length === 0 ? (
        <EmptyState
          className="mt-8 border-amber-200/15"
          title="No notifications yet"
          description="Customer SMS updates appear here after orders are placed."
        />
      ) : null}
    </main>
  );
}
