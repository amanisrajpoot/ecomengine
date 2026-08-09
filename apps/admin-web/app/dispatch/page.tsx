"use client";

import { ApiError } from "@commerce/api-client";
import type { Delivery, Order } from "@commerce/types";
import { DispatchPanel, Spinner, StatusBadge } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, getTenantId, getToken } from "../../lib/session";

export default function DispatchPage() {
  const router = useRouter();
  const [orders, setOrders] = useState<Order[]>([]);
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [partnerNames, setPartnerNames] = useState<Map<string, string>>(new Map());
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    if (!getTenantId()) {
      setError("Select a tenant on the Tenants page first.");
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const client = api();
        const [orderRows, deliveryRows, partnerRows] = await Promise.all([
          client.listOrders(),
          client.listDeliveries({ active_only: true }),
          client.listDeliveryPartners({ status: "ACTIVE" }),
        ]);
        if (!cancelled) {
          setOrders(orderRows);
          setDeliveries(deliveryRows);
          setPartnerNames(
            new Map(
              partnerRows.map((p) => [p.id, p.display_name ?? `Rider ${p.id.slice(0, 8)}…`]),
            ),
          );
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load dispatch queue");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    const timer = window.setInterval(() => {
      Promise.all([
        api().listDeliveries({ active_only: true }),
        api().listDeliveryPartners({ status: "ACTIVE" }),
      ])
        .then(([deliveryRows, partnerRows]) => {
          setDeliveries(deliveryRows);
          setPartnerNames(
            new Map(
              partnerRows.map((p) => [p.id, p.display_name ?? `Rider ${p.id.slice(0, 8)}…`]),
            ),
          );
        })
        .catch(() => undefined);
    }, 8000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [router]);

  const awaiting = orders.filter(
    (o) =>
      ["READY", "PAYMENT_CONFIRMED"].includes(o.status) &&
      o.fulfillment_type !== "SELF_PICKUP" &&
      !deliveries.some(
        (d) =>
          d.metadata &&
          typeof d.metadata === "object" &&
          "order_id" in d.metadata &&
          d.metadata.order_id === o.id &&
          d.partner_id,
      ),
  );

  const client = api();

  return (
    <main className="mx-auto max-w-5xl px-5 py-10">
      <p className="font-display text-4xl text-violet-50">Dispatch</p>
      <p className="mt-2 text-sm text-violet-100/55">
        Orders waiting for rider assignment and active deliveries in this tenant.
      </p>
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-violet-300" />
        </div>
      ) : (
        <>
          <section className="mt-8">
            <h2 className="text-sm uppercase tracking-wide text-violet-200/50">
              Awaiting rider ({awaiting.length})
            </h2>
            <ul className="mt-3 flex flex-col gap-4">
              {awaiting.map((order) => (
                <li
                  key={order.id}
                  className="rounded-2xl border border-violet-200/10 bg-violet-950/25 p-5"
                >
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <StatusBadge status={order.status} />
                      <p className="mt-2 text-sm text-violet-100/60">
                        {order.state_machine_profile} · {order.id.slice(0, 8)}…
                      </p>
                    </div>
                    <Link
                      href={`/orders/${order.id}/debugger`}
                      className="text-xs text-violet-300 hover:text-violet-100"
                    >
                      Debugger →
                    </Link>
                  </div>
                  <DispatchPanel
                    order={order}
                    api={client}
                    className="mt-4 border-violet-200/15"
                  />
                </li>
              ))}
            </ul>
            {awaiting.length === 0 ? (
              <p className="mt-4 text-sm text-violet-100/55">No orders waiting for riders.</p>
            ) : null}
          </section>

          <section className="mt-10">
            <h2 className="text-sm uppercase tracking-wide text-violet-200/50">
              Active deliveries ({deliveries.length})
            </h2>
            <ul className="mt-3 flex flex-col gap-2">
              {deliveries.map((delivery) => (
                <li
                  key={delivery.id}
                  className="flex items-center justify-between rounded-xl border border-violet-200/10 px-4 py-3"
                >
                  <div>
                    <StatusBadge status={delivery.status} />
                    <p className="mt-1 text-xs text-violet-100/50">{delivery.id.slice(0, 8)}…</p>
                  </div>
                  <p className="text-xs text-violet-100/60">
                    {delivery.partner_id
                      ? partnerNames.get(delivery.partner_id) ??
                        `Rider ${delivery.partner_id.slice(0, 8)}…`
                      : "Unassigned"}
                  </p>
                </li>
              ))}
            </ul>
          </section>
        </>
      )}
    </main>
  );
}
