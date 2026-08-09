"use client";

import { ApiError } from "@commerce/api-client";
import type { Delivery, Partner } from "@commerce/types";
import { Button, EmptyState, Spinner, StatusBadge } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, DEMO_LAT, DEMO_LNG, getToken } from "../../lib/session";

const POLL_MS = 10000;

export default function DeliveriesPage() {
  const router = useRouter();
  const [partner, setPartner] = useState<Partner | null>(null);
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const rows = await api().listDeliveries({ mine: true, active_only: true });
    setDeliveries(rows);
  }, []);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const p = await api().getMyPartner();
        if (cancelled) return;
        setPartner(p);
        await refresh();
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load rider profile");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refresh, router]);

  useEffect(() => {
    if (loading) return;
    const timer = window.setInterval(() => {
      refresh().catch(() => undefined);
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [loading, refresh]);

  async function toggleOnline() {
    if (!partner) return;
    setBusy(true);
    setError(null);
    try {
      const updated = await api().updateMyLocation({
        lat: partner.current_lat ?? DEMO_LAT,
        lng: partner.current_lng ?? DEMO_LNG,
        is_online: !partner.is_online,
      });
      setPartner(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update status");
    } finally {
      setBusy(false);
    }
  }

  async function goOnlineWithPing() {
    setBusy(true);
    setError(null);
    try {
      const updated = await api().updateMyLocation({
        lat: DEMO_LAT,
        lng: DEMO_LNG,
        is_online: true,
      });
      setPartner(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Location update failed");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto flex max-w-3xl justify-center px-5 py-20">
        <Spinner size="lg" className="text-sky-300" />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <p className="font-display text-4xl text-sky-50">Jobs</p>

      {partner ? (
        <div className="mt-6 rounded-2xl border border-sky-200/10 bg-sky-950/30 p-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <p className="text-sm text-sky-100/55">Availability</p>
              <div className="mt-1 flex items-center gap-2">
                <span
                  className={`h-2.5 w-2.5 rounded-full ${
                    partner.is_online ? "bg-emerald-400" : "bg-slate-500"
                  }`}
                />
                <p className="text-lg font-medium text-sky-50">
                  {partner.is_online ? "You're online" : "You're offline"}
                </p>
              </div>
              <p className="mt-1 text-xs text-sky-100/45">
                {partner.is_online
                  ? "Dispatch can assign new deliveries to you."
                  : "Go online to receive assignments."}
              </p>
            </div>
            <div className="flex flex-col gap-2 sm:flex-row">
              {partner.is_online ? (
                <Button
                  type="button"
                  variant="ghost"
                  disabled={busy}
                  className="border border-sky-300/20 text-sky-100"
                  onClick={toggleOnline}
                >
                  Go offline
                </Button>
              ) : (
                <Button
                  type="button"
                  disabled={busy}
                  className="bg-sky-500 text-sky-950 hover:bg-sky-400"
                  onClick={goOnlineWithPing}
                >
                  Go online
                </Button>
              )}
            </div>
          </div>
        </div>
      ) : null}

      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      <ul className="mt-8 flex flex-col gap-3">
        {deliveries.map((delivery) => {
          const completed = delivery.stops.filter((s) => s.status === "COMPLETED").length;
          const nextStop = delivery.stops.find((s) => s.status !== "COMPLETED");
          return (
            <li key={delivery.id}>
              <Link
                href={`/deliveries/${delivery.id}`}
                className="block rounded-2xl border border-sky-200/10 bg-sky-950/25 px-5 py-4 transition hover:border-sky-300/25"
              >
                <div className="flex items-start justify-between gap-3">
                  <StatusBadge status={delivery.status} />
                  <span className="text-xs text-sky-100/50">
                    {completed}/{delivery.stops.length} stops done
                  </span>
                </div>
                {nextStop ? (
                  <p className="mt-3 text-sm text-sky-50">
                    Next: {nextStop.stop_type}
                    {typeof nextStop.address?.line1 === "string"
                      ? ` · ${nextStop.address.line1}`
                      : ""}
                  </p>
                ) : null}
                <p className="mt-1 text-xs text-sky-100/45">Tap for step-by-step POD</p>
              </Link>
            </li>
          );
        })}
      </ul>

      {!error && deliveries.length === 0 ? (
        <EmptyState
          className="mt-8 border-sky-200/15"
          title="No active jobs"
          description={
            partner?.is_online
              ? "Waiting for dispatch to assign a delivery."
              : "Go online to start receiving assignments."
          }
        />
      ) : null}
    </main>
  );
}
