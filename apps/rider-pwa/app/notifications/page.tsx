"use client";

import { ApiError } from "@commerce/api-client";
import type { Notification } from "@commerce/types";
import { EmptyState, NotificationCard, Spinner } from "@commerce/ui";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, getToken } from "../../lib/session";

export default function RiderNotificationsPage() {
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
    <main className="mx-auto max-w-xl px-5 py-10">
      <p className="font-display text-4xl text-sky-50">Alerts</p>
      <p className="mt-2 text-sm text-sky-100/55">
        Order updates for deliveries assigned to you.
      </p>

      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-sky-300" />
        </div>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      <ul className="mt-8 flex flex-col gap-3">
        {rows.map((notification) => (
          <li key={notification.id}>
            <NotificationCard
              notification={notification}
              className="!border-sky-200/10 !bg-sky-950/25"
            />
          </li>
        ))}
      </ul>

      {!loading && !error && rows.length === 0 ? (
        <EmptyState
          className="mt-8 border-sky-200/15"
          title="No alerts yet"
          description="Accept a delivery job — order SMS updates for those orders appear here."
        />
      ) : null}
    </main>
  );
}
