"use client";

import { ApiError } from "@commerce/api-client";
import type { Order, OrderDeliveryTracking } from "@commerce/types";
import { useCallback } from "react";

import { ErrorState } from "./error-state";
import { LiveIndicator } from "./live-indicator";
import { StatusBadge } from "./status-badge";
import { usePolling } from "./hooks/use-polling";

type TrackingApi = {
  getOrderDelivery: (orderId: string) => Promise<OrderDeliveryTracking>;
};

type TrackingData = OrderDeliveryTracking | null;

type OrderTrackingPanelProps = {
  order: Order;
  api: TrackingApi;
  className?: string;
};

const TERMINAL_ORDER = new Set(["DELIVERED", "CANCELLED", "FAILED", "REFUNDED"]);
const TRACKABLE = new Set([
  "ACCEPTED",
  "PREPARING",
  "PICKING",
  "PACKING",
  "READY",
  "PICKED_UP",
  "OUT_FOR_DELIVERY",
  "IN_TRANSIT",
  "PAYMENT_CONFIRMED",
  "PICKUP_ASSIGNED",
  "DELIVERED",
]);

function stopLabel(stopType: string): string {
  if (stopType === "PICKUP") return "Pickup";
  if (stopType === "DROP") return "Drop-off";
  return stopType;
}

function formatEta(eta: string | null): string | null {
  if (!eta) return null;
  try {
    return new Date(eta).toLocaleString("en-IN", {
      hour: "numeric",
      minute: "2-digit",
      day: "numeric",
      month: "short",
    });
  } catch {
    return null;
  }
}

export function OrderTrackingPanel({ order, api, className = "" }: OrderTrackingPanelProps) {
  const shouldTrack =
    order.fulfillment_type !== "SELF_PICKUP" &&
    (order.state_machine_profile === "COURIER" || TRACKABLE.has(order.status) || order.status === "DELIVERED");

  const fetcher = useCallback(async (): Promise<TrackingData> => {
    try {
      return await api.getOrderDelivery(order.id);
    } catch (err) {
      if (err instanceof ApiError && err.status === 404) return null;
      throw err;
    }
  }, [api, order.id]);

  const { data: tracking, error, loading, refresh } = usePolling(fetcher, {
    intervalMs: 5000,
    enabled: shouldTrack && !TERMINAL_ORDER.has(order.status),
    immediate: shouldTrack,
  });

  if (!shouldTrack) return null;

  const dropAddress =
    typeof order.metadata?.drop === "object" && order.metadata.drop
      ? (order.metadata.drop as { address?: { line1?: string; city?: string } }).address
      : null;

  return (
    <section
      className={`rounded-2xl border border-emerald-200/10 bg-emerald-950/30 px-4 py-4 ${className}`}
    >
      <div className="flex items-center justify-between gap-2">
        <p className="text-sm font-medium text-emerald-50">Delivery tracking</p>
        {!TERMINAL_ORDER.has(order.status) ? <LiveIndicator /> : null}
      </div>
      {dropAddress?.line1 ? (
        <p className="mt-1 text-xs text-emerald-100/50">
          {dropAddress.line1}
          {dropAddress.city ? `, ${dropAddress.city}` : ""}
        </p>
      ) : null}

      {loading && !tracking ? (
        <p className="mt-3 text-sm text-emerald-100/45">Loading tracking…</p>
      ) : null}

      {error && !tracking ? (
        <ErrorState
          className="mt-3 !border-rose-400/15 !bg-rose-950/15 !py-6"
          title="Tracking unavailable"
          message={error}
          onRetry={() => void refresh()}
        />
      ) : null}

      {tracking ? (
        <div className="mt-3 space-y-3 text-sm text-emerald-100/75">
          {tracking.fulfillment_status ? (
            <p>
              Fulfillment{" "}
              <StatusBadge status={tracking.fulfillment_status} className="!text-[10px]" />
            </p>
          ) : null}
          <p>
            Delivery <StatusBadge status={tracking.status} className="!text-[10px]" />
          </p>
          {tracking.partner?.display_name ? (
            <p className="text-xs text-emerald-200/70">
              Rider: {tracking.partner.display_name}
            </p>
          ) : tracking.status !== "COMPLETED" && tracking.status !== "CANCELLED" ? (
            <p className="text-xs text-amber-200/70">Finding a rider…</p>
          ) : null}
          {formatEta(tracking.eta) ? (
            <p className="text-xs text-emerald-100/55">ETA {formatEta(tracking.eta)}</p>
          ) : null}
          {tracking.last_location ? (
            <p className="text-xs text-emerald-100/45">
              Last known location: {tracking.last_location.lat.toFixed(4)},{" "}
              {tracking.last_location.lng.toFixed(4)}
            </p>
          ) : null}
          {tracking.stops.length ? (
            <ul className="space-y-2 border-t border-emerald-200/10 pt-3">
              {tracking.stops.map((stop) => {
                const addr = stop.address as { line1?: string; city?: string };
                return (
                  <li key={stop.id} className="flex items-start justify-between gap-3 text-xs">
                    <div>
                      <p className="font-medium text-emerald-50/90">{stopLabel(stop.stop_type)}</p>
                      {addr?.line1 ? (
                        <p className="text-emerald-100/45">
                          {addr.line1}
                          {addr.city ? `, ${addr.city}` : ""}
                        </p>
                      ) : null}
                    </div>
                    <StatusBadge status={stop.status} className="!text-[10px] shrink-0" />
                  </li>
                );
              })}
            </ul>
          ) : null}
        </div>
      ) : !loading && !error ? (
        <p className="mt-3 text-xs text-emerald-100/45">
          Rider will be assigned when your order is ready.
        </p>
      ) : null}

      {error && tracking ? (
        <p className="mt-3 text-xs text-rose-300/80">Could not refresh: {error}</p>
      ) : null}
    </section>
  );
}
