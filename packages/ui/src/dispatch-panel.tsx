"use client";

import { ApiError } from "@commerce/api-client";
import type { Delivery, Fulfillment, Order, Partner } from "@commerce/types";
import { Button, StatusBadge } from "@commerce/ui";
import { useCallback, useEffect, useState } from "react";

type DispatchApi = {
  getOrderFulfillment: (orderId: string) => Promise<Fulfillment>;
  getFulfillmentDelivery: (fulfillmentId: string) => Promise<Delivery>;
  createDelivery: (fulfillmentId: string) => Promise<Delivery>;
  listDeliveryPartners?: (params?: {
    online_only?: boolean;
    status?: string;
  }) => Promise<Partner[]>;
  assignDelivery: (
    deliveryId: string,
    body?: { partner_id?: string },
  ) => Promise<Delivery>;
};

type DispatchPanelProps = {
  order: Order;
  api: DispatchApi;
  onUpdate?: () => void;
  className?: string;
};

const DISPATCHABLE = new Set([
  "READY",
  "PICKED_UP",
  "OUT_FOR_DELIVERY",
  "PAYMENT_CONFIRMED",
  "PICKUP_ASSIGNED",
]);

export function DispatchPanel({ order, api, onUpdate, className = "" }: DispatchPanelProps) {
  const [fulfillment, setFulfillment] = useState<Fulfillment | null>(null);
  const [delivery, setDelivery] = useState<Delivery | null>(null);
  const [partners, setPartners] = useState<Partner[]>([]);
  const [selectedPartnerId, setSelectedPartnerId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [notFound, setNotFound] = useState(false);

  const load = useCallback(async () => {
    if (!DISPATCHABLE.has(order.status) && order.state_machine_profile !== "COURIER") {
      return;
    }
    if (order.fulfillment_type === "SELF_PICKUP") return;

    try {
      const ful = await api.getOrderFulfillment(order.id);
      setFulfillment(ful);
      try {
        const del = await api.getFulfillmentDelivery(ful.id);
        setDelivery(del);
        setNotFound(false);
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          setDelivery(null);
          setNotFound(true);
        } else {
          throw err;
        }
      }
      setError(null);
    } catch (err) {
      if (!(err instanceof ApiError && err.status === 404)) {
        setError(err instanceof ApiError ? err.message : "Could not load dispatch status");
      }
    }
  }, [api, order.fulfillment_type, order.id, order.state_machine_profile, order.status]);

  const loadPartners = useCallback(async () => {
    if (!api.listDeliveryPartners) return;
    try {
      const rows = await api.listDeliveryPartners({ online_only: true, status: "ACTIVE" });
      setPartners(rows);
      if (!selectedPartnerId && rows[0]?.id) {
        setSelectedPartnerId(rows[0].id);
      }
    } catch {
      setPartners([]);
    }
  }, [api, selectedPartnerId]);

  useEffect(() => {
    void load();
  }, [load]);

  useEffect(() => {
    if (!DISPATCHABLE.has(order.status) && order.status !== "DELIVERED") return;
    const timer = window.setInterval(() => {
      void load();
    }, 5000);
    return () => window.clearInterval(timer);
  }, [load, order.status]);

  const needsRider =
    fulfillment &&
    (!delivery || (delivery.status === "CREATED" && !delivery.partner_id));

  useEffect(() => {
    if (needsRider && api.listDeliveryPartners) {
      void loadPartners();
    }
  }, [api.listDeliveryPartners, loadPartners, needsRider]);

  async function assign(partnerId?: string) {
    if (!fulfillment) return;
    setBusy(true);
    setError(null);
    try {
      let del = delivery;
      if (!del) {
        del = await api.createDelivery(fulfillment.id);
        setDelivery(del);
        setNotFound(false);
      }
      if (!del.partner_id && del.status === "CREATED") {
        del = await api.assignDelivery(
          del.id,
          partnerId ? { partner_id: partnerId } : undefined,
        );
        setDelivery(del);
      }
      onUpdate?.();
    } catch (err) {
      const message =
        err instanceof ApiError
          ? err.code === "NO_PARTNERS_AVAILABLE"
            ? "No online riders available. Ask a rider to go online, then retry."
            : err.message
          : "Dispatch failed";
      setError(message);
    } finally {
      setBusy(false);
    }
  }

  if (order.fulfillment_type === "SELF_PICKUP") return null;
  if (
    order.state_machine_profile === "COURIER" &&
    !["PAYMENT_CONFIRMED", "PICKUP_ASSIGNED", "PICKED_UP", "IN_TRANSIT", "DELIVERED"].includes(
      order.status,
    )
  ) {
    return null;
  }
  if (
    order.state_machine_profile !== "COURIER" &&
    !DISPATCHABLE.has(order.status) &&
    order.status !== "DELIVERED"
  ) {
    return null;
  }

  return (
    <section
      className={`rounded-2xl border border-white/10 bg-black/20 px-4 py-4 ${className}`}
    >
      <p className="text-sm font-medium text-white/80">Dispatch</p>
      {fulfillment ? (
        <p className="mt-1 text-xs text-white/45">
          Fulfillment <StatusBadge status={fulfillment.status} className="!text-[10px]" />
        </p>
      ) : null}
      {delivery ? (
        <div className="mt-3 space-y-1 text-sm text-white/70">
          <p>
            Delivery <StatusBadge status={delivery.status} className="!text-[10px]" />
          </p>
          {delivery.partner_id ? (
            <p className="text-xs text-emerald-200/80">
              Rider assigned · {delivery.partner_id.slice(0, 8)}…
            </p>
          ) : (
            <p className="text-xs text-amber-200/70">Waiting for rider assignment</p>
          )}
        </div>
      ) : notFound ? (
        <p className="mt-3 text-sm text-amber-200/70">No delivery created yet.</p>
      ) : (
        <p className="mt-3 text-sm text-white/45">Loading dispatch status…</p>
      )}

      {needsRider ? (
        <div className="mt-4 flex flex-col gap-2">
          {api.listDeliveryPartners && partners.length > 0 ? (
            <label className="flex flex-col gap-1 text-xs text-white/55">
              <span>Assign rider</span>
              <select
                className="rounded-lg border border-white/10 bg-black/30 px-2 py-2 text-sm text-white/85"
                value={selectedPartnerId}
                onChange={(e) => setSelectedPartnerId(e.target.value)}
              >
                {partners.map((partner) => (
                  <option key={partner.id} value={partner.id}>
                    {partner.display_name ?? partner.id.slice(0, 8)}…
                    {partner.is_online ? " · online" : ""}
                  </option>
                ))}
              </select>
            </label>
          ) : null}
          <div className="flex flex-wrap gap-2">
            {api.listDeliveryPartners && partners.length > 0 && selectedPartnerId ? (
              <Button
                type="button"
                variant="soft"
                disabled={busy}
                onClick={() => void assign(selectedPartnerId)}
              >
                {busy ? "Assigning…" : "Assign selected"}
              </Button>
            ) : null}
            <Button
              type="button"
              variant="ghost"
              className="!text-xs"
              disabled={busy}
              onClick={() => void assign()}
            >
              Auto-assign nearest
            </Button>
          </div>
        </div>
      ) : null}

      {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
      {!needsRider && delivery?.partner_id ? (
        <p className="mt-3 text-xs text-white/40">Rider can complete pickup in the Rider app.</p>
      ) : null}
    </section>
  );
}
