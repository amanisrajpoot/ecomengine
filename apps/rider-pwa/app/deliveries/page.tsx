"use client";

import { ApiError } from "@commerce/api-client";
import type { Delivery, Partner } from "@commerce/types";
import { Button } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, DEMO_LAT, DEMO_LNG, getToken } from "../../lib/session";

export default function DeliveriesPage() {
  const router = useRouter();
  const [partner, setPartner] = useState<Partner | null>(null);
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

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
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [refresh, router]);

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

  async function pingLocation() {
    setBusy(true);
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

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <p className="font-display text-4xl text-sky-50">Jobs</p>
      {partner ? (
        <div className="mt-4 flex flex-wrap items-center gap-3">
          <span
            className={`rounded-full px-3 py-1 text-xs font-medium ${
              partner.is_online
                ? "bg-emerald-400/20 text-emerald-200"
                : "bg-slate-400/20 text-slate-300"
            }`}
          >
            {partner.is_online ? "Online" : "Offline"}
          </span>
          <Button
            type="button"
            variant="soft"
            disabled={busy}
            className="border border-sky-300/20 bg-sky-400/10 text-sky-50"
            onClick={toggleOnline}
          >
            {partner.is_online ? "Go offline" : "Go online"}
          </Button>
          <Button
            type="button"
            variant="ghost"
            disabled={busy}
            className="text-sky-100/70"
            onClick={pingLocation}
          >
            Ping location
          </Button>
        </div>
      ) : null}

      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      <ul className="mt-8 flex flex-col gap-3">
        {deliveries.map((delivery) => (
          <li key={delivery.id}>
            <Link
              href={`/deliveries/${delivery.id}`}
              className="block rounded-2xl border border-sky-200/10 bg-sky-950/25 px-5 py-4 transition hover:border-sky-300/25"
            >
              <div className="flex items-baseline justify-between gap-3">
                <p className="font-medium text-sky-50">{delivery.status}</p>
                <span className="text-xs text-sky-100/50">
                  {delivery.stops.filter((s) => s.status === "COMPLETED").length}/
                  {delivery.stops.length} stops
                </span>
              </div>
              <p className="mt-1 text-xs text-sky-100/45">{delivery.id.slice(0, 8)}…</p>
            </Link>
          </li>
        ))}
      </ul>
      {!error && deliveries.length === 0 ? (
        <p className="mt-8 text-sm text-sky-100/55">
          No active assignments. Go online and wait for dispatch to assign a delivery.
        </p>
      ) : null}
    </main>
  );
}
