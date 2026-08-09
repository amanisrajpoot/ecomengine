"use client";

import { ApiError } from "@commerce/api-client";
import type { Delivery, DeliveryStop } from "@commerce/types";
import { Button } from "@commerce/ui";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, DEMO_LAT, DEMO_LNG, getToken } from "../../../lib/session";

function stopLabel(stop: DeliveryStop): string {
  const line =
    typeof stop.address?.line1 === "string" ? stop.address.line1 : stop.stop_type;
  return `${stop.stop_type} · ${line}`;
}

export default function DeliveryDetailPage() {
  const router = useRouter();
  const params = useParams<{ deliveryId: string }>();
  const [delivery, setDelivery] = useState<Delivery | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busyStop, setBusyStop] = useState<string | null>(null);

  const load = useCallback(async () => {
    const data = await api().getDelivery(params.deliveryId);
    setDelivery(data);
    if (data.status !== "COMPLETED" && data.status !== "CANCELLED") {
      await api().updateDeliveryTracking(params.deliveryId, {
        lat: DEMO_LAT,
        lng: DEMO_LNG,
      });
    }
  }, [params.deliveryId]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        await load();
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Delivery not found");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [load, router]);

  async function completeStop(stop: DeliveryStop) {
    setBusyStop(stop.id);
    setError(null);
    const proof =
      stop.stop_type === "PICKUP"
        ? { otp: "1234" }
        : { photo_url: "https://cdn.example/rider-pod.jpg", otp: "5678" };
    try {
      const updated = await api().completeDeliveryStop(
        params.deliveryId,
        stop.id,
        proof,
      );
      setDelivery(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not complete stop");
    } finally {
      setBusyStop(null);
    }
  }

  return (
    <main className="mx-auto max-w-xl px-5 py-10">
      <p className="font-display text-4xl text-sky-50">Delivery</p>
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      {delivery ? (
        <div className="mt-8 space-y-5">
          <p className="text-2xl text-sky-50">{delivery.status}</p>
          <ul className="flex flex-col gap-3">
            {delivery.stops.map((stop) => (
              <li
                key={stop.id}
                className="rounded-2xl border border-sky-200/10 bg-sky-950/25 px-4 py-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium text-sky-50">{stopLabel(stop)}</p>
                    <p className="text-xs text-sky-100/50">
                      {stop.lat != null ? `${stop.lat.toFixed(4)}, ${stop.lng?.toFixed(4)}` : "—"}
                    </p>
                    <p className="mt-1 text-xs uppercase tracking-wide text-sky-200/45">
                      {stop.status}
                    </p>
                  </div>
                  {stop.status !== "COMPLETED" ? (
                    <Button
                      type="button"
                      variant="soft"
                      disabled={busyStop === stop.id}
                      className="shrink-0 bg-sky-500/20 text-sky-50"
                      onClick={() => completeStop(stop)}
                    >
                      {busyStop === stop.id ? "…" : "Complete"}
                    </Button>
                  ) : null}
                </div>
              </li>
            ))}
          </ul>
          {delivery.status === "COMPLETED" ? (
            <p className="text-sm text-emerald-200/80">Delivery complete — order synced.</p>
          ) : null}
        </div>
      ) : null}
    </main>
  );
}
