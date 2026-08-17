"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import type {
  Delivery,
  Fulfillment,
  LedgerPostingGroup,
  OrderDetail,
  Payment,
  PriceBreakdown,
  Settlement,
} from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Card, PriceDisplay } from "@commerce/ui";

import { getApiClient } from "@/lib/api";

function pricingFromSnapshot(snapshot: Record<string, unknown>): PriceBreakdown | null {
  if (typeof snapshot.total_paise !== "number") return null;
  return snapshot as unknown as PriceBreakdown;
}

export default function OrderDebuggerPage() {
  const params = useParams<{ orderId: string }>();
  const orderId = params.orderId;

  const [order, setOrder] = useState<OrderDetail | null>(null);
  const [fulfillment, setFulfillment] = useState<Fulfillment | null>(null);
  const [delivery, setDelivery] = useState<Delivery | null>(null);
  const [payments, setPayments] = useState<Payment[]>([]);
  const [ledger, setLedger] = useState<LedgerPostingGroup[]>([]);
  const [settlements, setSettlements] = useState<Settlement[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      const api = getApiClient();
      try {
        const detail = await api.getOrder(orderId);
        setOrder(detail);

        try {
          const pays = await api.listOrderPayments(orderId);
          setPayments(pays);
        } catch {
          setPayments([]);
        }

        try {
          const f = await api.getOrderFulfillment(orderId);
          setFulfillment(f);
          try {
            const d = await api.getFulfillmentDelivery(f.id);
            setDelivery(d);
          } catch {
            setDelivery(null);
          }
        } catch {
          setFulfillment(null);
          setDelivery(null);
        }

        try {
          const ledgerGroups = await api.listOrderLedgerEntries(orderId);
          setLedger(ledgerGroups);
        } catch {
          setLedger([]);
        }

        try {
          const settlementList = await api.listOrderSettlements(orderId);
          setSettlements(settlementList);
        } catch {
          setSettlements([]);
        }
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load order");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [orderId]);

  const pricing = order ? pricingFromSnapshot(order.pricing_snapshot) : null;

  return (
    <div className="space-y-4">
      <Link href="/orders" className="text-xs text-violet-300/70 hover:text-violet-100">
        ← Orders
      </Link>
      <h1 className="text-2xl font-semibold">Order debugger</h1>
      <p className="text-sm text-violet-200/70">
        Order → Fulfillment → Delivery → Ledger → Settlement
      </p>
      {loading ? <p className="text-sm text-violet-200/60">Loading trace…</p> : null}
      {error ? <p className="text-sm text-red-300">{error}</p> : null}

      {order ? (
        <Card title="1. Order">
          <p className="font-medium">{order.status}</p>
          <p className="font-mono text-xs text-violet-300/60">{order.id}</p>
          <p className="text-sm text-violet-200/70">
            {order.state_machine_profile} · {order.fulfillment_type}
          </p>
          {pricing ? (
            <p className="mt-2 text-lg">
              <PriceDisplay paise={pricing.total_paise} />
            </p>
          ) : null}
          {order.items && order.items.length > 0 ? (
            <ul className="mt-3 space-y-1 text-sm">
              {order.items.map((item) => (
                <li key={item.id}>
                  {item.name_snapshot} × {item.quantity} —{" "}
                  <PriceDisplay paise={item.unit_price_paise * item.quantity} />
                </li>
              ))}
            </ul>
          ) : null}
          {order.status_events && order.status_events.length > 0 ? (
            <ul className="mt-3 space-y-1 text-xs text-violet-300/70">
              {order.status_events.map((e) => (
                <li key={e.id}>{e.to_status} · {e.created_at}</li>
              ))}
            </ul>
          ) : null}
        </Card>
      ) : null}

      {payments.length > 0 ? (
        <Card title="Payments">
          <ul className="space-y-1 text-sm">
            {payments.map((p) => (
              <li key={p.id} className="flex justify-between gap-2">
                <span>{p.provider} · {p.status}</span>
                <PriceDisplay paise={p.amount_paise} />
              </li>
            ))}
          </ul>
        </Card>
      ) : null}

      <Card title="2. Fulfillment">
        {fulfillment ? (
          <>
            <p className="font-medium">{fulfillment.status}</p>
            <p className="text-sm text-violet-200/70">{fulfillment.type}</p>
            <p className="font-mono text-xs text-violet-300/60">{fulfillment.id}</p>
          </>
        ) : (
          <p className="text-sm text-violet-200/60">No fulfillment linked.</p>
        )}
      </Card>

      <Card title="3. Delivery">
        {delivery ? (
          <>
            <p className="font-medium">{delivery.status}</p>
            <p className="font-mono text-xs text-violet-300/60">{delivery.id}</p>
            <p className="text-sm text-violet-200/70">
              Partner: {delivery.partner_id ?? "—"}
            </p>
            {delivery.stops && delivery.stops.length > 0 ? (
              <ul className="mt-2 space-y-1 text-sm">
                {delivery.stops
                  .sort((a, b) => a.sequence - b.sequence)
                  .map((stop) => (
                    <li key={stop.id}>
                      {stop.stop_type} · {stop.status}
                      {stop.completed_at ? ` · ${stop.completed_at}` : ""}
                    </li>
                  ))}
              </ul>
            ) : null}
          </>
        ) : (
          <p className="text-sm text-violet-200/60">No delivery created yet.</p>
        )}
      </Card>

      <Card title="4. Ledger">
        {ledger.length === 0 ? (
          <p className="text-sm text-violet-200/60">No ledger postings.</p>
        ) : (
          <ul className="space-y-3">
            {ledger.map((group) => (
              <li key={group.event_group_id} className="rounded-lg bg-emerald-950/30 p-3 text-sm">
                <p className="font-medium">{group.event_type}</p>
                <ul className="mt-2 space-y-1 text-xs">
                  {group.entries.map((entry) => (
                    <li key={entry.id} className="flex justify-between gap-2">
                      <span>
                        {entry.account} {entry.direction}
                      </span>
                      <PriceDisplay paise={entry.amount_paise} />
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card title="5. Settlement">
        {settlements.length === 0 ? (
          <p className="text-sm text-violet-200/60">No settlements linked to this order.</p>
        ) : (
          <ul className="space-y-2 text-sm">
            {settlements.map((s) => (
              <li key={s.id} className="flex justify-between gap-2">
                <span>
                  {s.party_type} · {s.status}
                </span>
                <PriceDisplay paise={s.total_paise} />
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
