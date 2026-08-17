"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import type { Delivery, DeliveryStop, Fulfillment, OrderDetail } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Button, Card, OrderTimeline, StatusBadge } from "@commerce/ui";
import type { TimelineStep } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import {
  defaultProof,
  formatAddress,
  formatTime,
  orderNeedsRiderAction,
  primaryRiderAction,
  stopIcon,
  stopsCompletedCount,
  stopsTotalCount,
} from "@/lib/deliveryHelpers";
import { riderTransitionsFor } from "@/lib/orderTransitions";

function stopTimelineSteps(stops: DeliveryStop[]): TimelineStep[] {
  const sorted = [...stops].sort((a, b) => a.sequence - b.sequence);
  const firstPending = sorted.findIndex((s) => s.status !== "COMPLETED");
  return sorted.map((stop, index) => ({
    id: stop.id,
    label: `${stop.stop_type} · ${formatAddress(stop.address)}`,
    time: stop.completed_at ? formatTime(stop.completed_at) : undefined,
    done: stop.status === "COMPLETED",
    active: index === firstPending,
  }));
}

export default function JobDetailPage() {
  const params = useParams<{ deliveryId: string }>();
  const deliveryId = params.deliveryId;

  const [delivery, setDelivery] = useState<Delivery | null>(null);
  const [fulfillment, setFulfillment] = useState<Fulfillment | null>(null);
  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState<string | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const api = getApiClient();
      const d = await api.getDelivery(deliveryId);
      setDelivery(d);
      const f = await api.getFulfillment(d.fulfillment_id);
      setFulfillment(f);
      const o = await api.getOrder(f.order_id);
      setOrder(o);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load job");
    } finally {
      setLoading(false);
    }
  }, [deliveryId]);

  useEffect(() => {
    load();
  }, [load]);

  async function completeStop(stop: DeliveryStop) {
    setBusy(stop.id);
    setError(null);
    try {
      const updated = await getApiClient().completeDeliveryStop(deliveryId, stop.id, {
        proof: defaultProof(stop),
      });
      setDelivery(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Stop completion failed");
    } finally {
      setBusy(null);
    }
  }

  async function transitionOrder(toStatus: string) {
    if (!order) return;
    setBusy(toStatus);
    setError(null);
    try {
      const updated = await getApiClient().transitionOrder(order.id, { to_status: toStatus });
      setOrder(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Order transition failed");
    } finally {
      setBusy(null);
    }
  }

  const nextOrderStatuses = order
    ? riderTransitionsFor(order.state_machine_profile, order.status)
    : [];
  const primaryAction = order
    ? primaryRiderAction(order.state_machine_profile, order.status)
    : null;
  const steps = useMemo(
    () => (delivery?.stops ? stopTimelineSteps(delivery.stops) : []),
    [delivery?.stops],
  );

  return (
    <div className="space-y-5">
      <Link href="/jobs" className="text-sm font-medium text-[var(--brand)]">
        ← Back to jobs
      </Link>

      {loading ? <p className="text-sm text-gray-500">Loading…</p> : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      {delivery ? (
        <div className="rounded-2xl bg-white p-5 shadow-sm">
          <div className="flex items-start justify-between gap-3">
            <div>
              <StatusBadge status={delivery.status} />
              <p className="mt-2 font-mono text-xs text-gray-400">{delivery.id}</p>
            </div>
            <div className="text-right">
              <p className="text-lg font-bold text-gray-900">
                {stopsCompletedCount(delivery)}/{stopsTotalCount(delivery)}
              </p>
              <p className="text-xs text-gray-500">stops done</p>
            </div>
          </div>
        </div>
      ) : null}

      {order && primaryAction && orderNeedsRiderAction(order.state_machine_profile, order.status) ? (
        <Button
          variant="brand"
          className="w-full py-4 text-base font-bold bg-[var(--brand)] hover:bg-[var(--brand-dark)]"
          disabled={busy !== null}
          onClick={() => transitionOrder(primaryAction)}
        >
          {busy === primaryAction
            ? "Updating…"
            : `Mark ${primaryAction.replace(/_/g, " ").toLowerCase()}`}
        </Button>
      ) : null}

      {nextOrderStatuses.length > 1 ? (
        <div className="flex flex-wrap gap-2">
          {nextOrderStatuses
            .filter((s) => s !== primaryAction)
            .map((status) => (
              <Button
                key={status}
                variant="secondary"
                className="border-gray-300 bg-gray-100 text-gray-800 hover:bg-gray-200"
                disabled={busy !== null}
                onClick={() => transitionOrder(status)}
              >
                {busy === status ? "…" : status.replace(/_/g, " ")}
              </Button>
            ))}
        </div>
      ) : null}

      {order ? (
        <Card variant="light" title="Order">
          <div className="flex items-center justify-between gap-3">
            <StatusBadge status={order.status} />
            <span className="text-xs text-gray-500">{order.state_machine_profile}</span>
          </div>
        </Card>
      ) : null}

      {delivery?.stops && delivery.stops.length > 0 ? (
        <Card variant="light" title="Route">
          <OrderTimeline steps={steps} />
          <ul className="mt-4 space-y-3">
            {delivery.stops
              .sort((a, b) => a.sequence - b.sequence)
              .map((stop) => (
                <li
                  key={stop.id}
                  className={`rounded-xl border p-4 ${
                    stop.status === "COMPLETED"
                      ? "border-gray-100 bg-gray-50"
                      : "border-blue-200 bg-blue-50/50"
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <span className="text-2xl leading-none">{stopIcon(stop.stop_type)}</span>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2">
                        <StatusBadge status={stop.stop_type} />
                        <StatusBadge status={stop.status} />
                      </div>
                      <p className="mt-2 text-sm font-medium text-gray-900">
                        {formatAddress(stop.address)}
                      </p>
                      {stop.status !== "COMPLETED" ? (
                        <Button
                          variant="brand"
                          className="mt-3 w-full bg-[var(--brand)] hover:bg-[var(--brand-dark)]"
                          disabled={busy !== null}
                          onClick={() => completeStop(stop)}
                        >
                          {busy === stop.id ? "Completing…" : "Complete with POD"}
                        </Button>
                      ) : (
                        <p className="mt-2 text-xs text-emerald-600">
                          Completed {formatTime(stop.completed_at)}
                        </p>
                      )}
                    </div>
                  </div>
                </li>
              ))}
          </ul>
        </Card>
      ) : null}

      {fulfillment ? (
        <p className="text-xs text-gray-400">
          Fulfillment {fulfillment.id.slice(0, 8)}… · {fulfillment.type} · {fulfillment.status}
        </p>
      ) : null}
    </div>
  );
}
