"use client";

import { ApiError } from "@commerce/api-client";
import type { OrderDebugger } from "@commerce/types";
import { formatPaise } from "@commerce/ui";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { JsonBlock } from "../../../../components/JsonBlock";
import { api, getTenantId, getToken } from "../../../../lib/session";

export default function OrderDebuggerPage() {
  const router = useRouter();
  const params = useParams<{ orderId: string }>();
  const [debug, setDebug] = useState<OrderDebugger | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    if (!getTenantId()) {
      setError("Tenant context required — set on login or via Tenants page.");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const data = await api().getOrderDebugger(params.orderId);
        if (!cancelled) setDebug(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Debugger unavailable");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [params.orderId, router]);

  const total =
    debug && typeof debug.order.pricing_snapshot?.total_paise === "number"
      ? debug.order.pricing_snapshot.total_paise
      : null;

  return (
    <main className="mx-auto max-w-5xl px-5 py-10">
      <Link href="/orders" className="text-sm text-violet-300/70 hover:text-violet-100">
        ← Orders
      </Link>
      <p className="mt-4 font-display text-4xl text-violet-50">Order debugger</p>
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      {debug ? (
        <div className="mt-8 space-y-6">
          <div className="rounded-2xl border border-violet-300/20 bg-violet-500/10 px-5 py-4">
            <div className="flex flex-wrap items-baseline justify-between gap-3">
              <div>
                <p className="text-2xl font-medium text-violet-50">{debug.order.status}</p>
                <p className="text-sm text-violet-100/60">
                  Vertical <span className="text-violet-200">{debug.vertical}</span> ·{" "}
                  {debug.order.state_machine_profile}
                </p>
              </div>
              <p className="font-display text-3xl text-violet-50">
                {total != null ? formatPaise(total) : "—"}
              </p>
            </div>
            <ol className="mt-4 flex flex-wrap gap-2">
              {debug.chain.map((step) => {
                const done =
                  (step === "order" && debug.order) ||
                  (step === "payments" && debug.payments.length > 0) ||
                  (step === "ledger" && debug.ledger_entries.length > 0) ||
                  (step === "fulfillment" && debug.fulfillment) ||
                  (step === "delivery" && debug.delivery) ||
                  (step === "settlements" && debug.settlements.length > 0);
                return (
                  <li
                    key={step}
                    className={`rounded-full px-3 py-1 text-xs uppercase tracking-wide ${
                      done
                        ? "bg-emerald-400/20 text-emerald-100"
                        : "bg-violet-950/40 text-violet-100/40"
                    }`}
                  >
                    {step}
                  </li>
                );
              })}
            </ol>
          </div>

          <JsonBlock title="Order" data={debug.order} />
          <JsonBlock title="Payments" data={debug.payments} />
          <JsonBlock title="Ledger entries" data={debug.ledger_entries} />
          <JsonBlock title="Ledger balances" data={debug.ledger_balances} />
          <JsonBlock title="Fulfillment" data={debug.fulfillment} />
          <JsonBlock title="Delivery" data={debug.delivery} />
          <JsonBlock title="Settlements" data={debug.settlements} />
        </div>
      ) : null}
    </main>
  );
}
