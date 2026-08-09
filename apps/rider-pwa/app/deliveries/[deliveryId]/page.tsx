"use client";

import { ApiError } from "@commerce/api-client";
import type { Delivery, DeliveryStop } from "@commerce/types";
import { Button, Spinner, StatusBadge } from "@commerce/ui";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

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
  const [loading, setLoading] = useState(true);
  const [busyStop, setBusyStop] = useState<string | null>(null);
  const [podOtp, setPodOtp] = useState("");

  const load = useCallback(async () => {
    const data = await api().getDelivery(params.deliveryId);
    setDelivery(data);
    if (data.status !== "COMPLETED" && data.status !== "CANCELLED") {
      await api().updateDeliveryTracking(params.deliveryId, {
        lat: DEMO_LAT,
        lng: DEMO_LNG,
      });
    }
    return data;
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
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [load, router]);

  const activeStop = useMemo(
    () => delivery?.stops.find((s) => s.status !== "COMPLETED") ?? null,
    [delivery],
  );

  async function completeStop(stop: DeliveryStop) {
    setBusyStop(stop.id);
    setError(null);
    const proof =
      stop.stop_type === "PICKUP"
        ? { otp: podOtp || "1234" }
        : { photo_url: "https://cdn.example/rider-pod.jpg", otp: podOtp || "5678" };
    try {
      const updated = await api().completeDeliveryStop(params.deliveryId, stop.id, proof);
      setDelivery(updated);
      setPodOtp("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not complete stop");
    } finally {
      setBusyStop(null);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto flex max-w-xl justify-center px-5 py-20">
        <Spinner size="lg" className="text-sky-300" />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-xl px-5 py-10">
      <p className="font-display text-4xl text-sky-50">Delivery</p>
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      {delivery ? (
        <div className="mt-8 space-y-5">
          <StatusBadge status={delivery.status} />

          <ol className="flex flex-col gap-0">
            {delivery.stops.map((stop, index) => {
              const done = stop.status === "COMPLETED";
              const active = activeStop?.id === stop.id;
              return (
                <li key={stop.id} className="flex gap-3">
                  <div className="flex flex-col items-center">
                    <span
                      className={`flex h-8 w-8 items-center justify-center rounded-full text-sm font-semibold ${
                        done
                          ? "bg-emerald-500 text-emerald-950"
                          : active
                            ? "bg-sky-400 text-sky-950 ring-2 ring-sky-300/50"
                            : "bg-white/10 text-white/40"
                      }`}
                    >
                      {done ? "✓" : index + 1}
                    </span>
                    {index < delivery.stops.length - 1 ? (
                      <span
                        className={`my-1 w-0.5 flex-1 ${done ? "bg-emerald-500/50" : "bg-white/10"}`}
                      />
                    ) : null}
                  </div>
                  <div
                    className={`mb-4 flex-1 rounded-2xl border px-4 py-3 ${
                      active
                        ? "border-sky-300/30 bg-sky-950/40"
                        : "border-sky-200/10 bg-sky-950/20"
                    }`}
                  >
                    <p className="font-medium text-sky-50">{stopLabel(stop)}</p>
                    <p className="mt-1 text-xs uppercase tracking-wide text-sky-200/45">
                      {stop.status}
                    </p>
                    {active && stop.status !== "COMPLETED" ? (
                      <div className="mt-4 space-y-3">
                        <p className="text-sm text-sky-100/70">
                          {stop.stop_type === "PICKUP"
                            ? "Confirm pickup with merchant OTP."
                            : "Confirm drop-off with customer OTP or photo proof."}
                        </p>
                        <label className="flex flex-col gap-1 text-sm text-sky-100/70">
                          <span>OTP (demo: {stop.stop_type === "PICKUP" ? "1234" : "5678"})</span>
                          <input
                            className="rounded-xl border border-sky-200/15 bg-sky-950/60 px-3 py-2 text-sky-50"
                            value={podOtp}
                            onChange={(e) => setPodOtp(e.target.value)}
                            placeholder="Enter OTP"
                          />
                        </label>
                        <Button
                          type="button"
                          variant="soft"
                          disabled={busyStop === stop.id}
                          className="w-full bg-sky-500/20 text-sky-50"
                          onClick={() => completeStop(stop)}
                        >
                          {busyStop === stop.id
                            ? "Completing…"
                            : `Complete ${stop.stop_type.toLowerCase()}`}
                        </Button>
                      </div>
                    ) : null}
                  </div>
                </li>
              );
            })}
          </ol>

          {delivery.status === "COMPLETED" ? (
            <p className="text-sm text-emerald-200/80">Delivery complete — order synced.</p>
          ) : null}
        </div>
      ) : null}
    </main>
  );
}
