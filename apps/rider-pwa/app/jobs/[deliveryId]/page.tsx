"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import type { Delivery, DeliveryStop, Fulfillment, OrderDetail } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Button, Card } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { riderTransitionsFor } from "@/lib/orderTransitions";

function formatAddress(address: Record<string, unknown>): string {
  const parts = [address.line1, address.city, address.pincode].filter(Boolean);
  return parts.join(", ") || "Address";
}

function defaultProof(stop: DeliveryStop): Record<string, unknown> {
  if (stop.stop_type === "PICKUP") {
    return { type: "OTP", code: "1234" };
  }
  return { type: "PHOTO", url: "s3://pod/rider-pwa.jpg" };
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

  return (
    <div className="space-y-4">
      <Link href="/jobs" className="text-xs text-sky-300/70 hover:text-sky-100">
        ← Jobs
      </Link>
      <h1 className="text-2xl font-semibold">Job detail</h1>
      {loading ? <p className="text-sm text-sky-200/60">Loading…</p> : null}
      {error ? <p className="text-sm text-red-300">{error}</p> : null}

      {delivery ? (
        <Card title="Delivery">
          <p className="font-medium">{delivery.status}</p>
          <p className="text-xs font-mono text-sky-300/60">{delivery.id}</p>
        </Card>
      ) : null}

      {order ? (
        <Card title="Order">
          <p className="font-medium">{order.status}</p>
          <p className="text-sm text-sky-200/70">{order.state_machine_profile}</p>
          {nextOrderStatuses.length > 0 ? (
            <div className="mt-3 flex flex-wrap gap-2">
              {nextOrderStatuses.map((status) => (
                <Button
                  key={status}
                  variant="secondary"
                  disabled={busy !== null}
                  onClick={() => transitionOrder(status)}
                >
                  {busy === status ? "…" : status.replace(/_/g, " ")}
                </Button>
              ))}
            </div>
          ) : null}
        </Card>
      ) : null}

      {delivery?.stops && delivery.stops.length > 0 ? (
        <Card title="Stops">
          <ul className="space-y-3">
            {delivery.stops
              .sort((a, b) => a.sequence - b.sequence)
              .map((stop) => (
                <li
                  key={stop.id}
                  className="rounded-lg bg-emerald-950/40 px-3 py-2 text-sm"
                >
                  <p className="font-medium">
                    {stop.stop_type} · {stop.status}
                  </p>
                  <p className="text-sky-200/70">{formatAddress(stop.address)}</p>
                  {stop.status !== "COMPLETED" ? (
                    <Button
                      className="mt-2"
                      variant="secondary"
                      disabled={busy !== null}
                      onClick={() => completeStop(stop)}
                    >
                      {busy === stop.id ? "Completing…" : "Complete with POD"}
                    </Button>
                  ) : null}
                </li>
              ))}
          </ul>
        </Card>
      ) : null}

      {fulfillment ? (
        <p className="text-xs text-sky-300/50">
          Fulfillment {fulfillment.id.slice(0, 8)}… · {fulfillment.type} · {fulfillment.status}
        </p>
      ) : null}
    </div>
  );
}
