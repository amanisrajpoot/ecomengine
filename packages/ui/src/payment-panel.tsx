"use client";

import { ApiError } from "@commerce/api-client";
import type { Order, Payment } from "@commerce/types";
import { Button, StatusBadge, formatPaise } from "@commerce/ui";
import { useCallback, useEffect, useState } from "react";

type PaymentApi = {
  listOrderPayments: (orderId: string) => Promise<Payment[]>;
  verifyOrderPayment: (
    orderId: string,
    body?: { provider?: string; provider_ref?: string },
  ) => Promise<{ payment: Payment; order_status: string }>;
};

type PaymentPanelProps = {
  order: Order;
  api: PaymentApi;
  onUpdate?: (orderStatus: string) => void;
  className?: string;
};

export function PaymentPanel({ order, api, onUpdate, className = "" }: PaymentPanelProps) {
  const [payments, setPayments] = useState<Payment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const rows = await api.listOrderPayments(order.id);
    setPayments(rows);
    return rows;
  }, [api, order.id]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await load();
        if (!cancelled) setError(null);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Could not load payment");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [load]);

  useEffect(() => {
    if (order.status !== "PAYMENT_PENDING") return;
    const timer = window.setInterval(() => {
      load().catch(() => undefined);
    }, 5000);
    return () => window.clearInterval(timer);
  }, [load, order.status]);

  async function completeMockPayment(payment: Payment) {
    setBusy(true);
    setError(null);
    try {
      const result = await api.verifyOrderPayment(order.id, {
        provider: payment.provider,
        provider_ref: payment.provider_ref ?? undefined,
      });
      setPayments([result.payment]);
      onUpdate?.(result.order_status);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Payment verification failed");
    } finally {
      setBusy(false);
    }
  }

  const payment = payments[0];
  const checkout = payment?.checkout_payload ?? {};
  const isMock = checkout.mode === "mock";
  const paymentUrl =
    typeof checkout.payment_url === "string" ? checkout.payment_url : null;
  const needsPayment = order.status === "PAYMENT_PENDING";

  if (!needsPayment && !payment) return null;

  return (
    <section
      className={`rounded-2xl border border-emerald-200/10 bg-emerald-950/30 px-4 py-4 ${className}`}
    >
      <p className="text-sm font-medium text-emerald-50">Payment</p>
      {loading ? (
        <p className="mt-3 text-sm text-emerald-100/45">Loading payment…</p>
      ) : payment ? (
        <div className="mt-3 space-y-3 text-sm text-emerald-100/75">
          <div className="flex flex-wrap items-center gap-2">
            <StatusBadge status={payment.status} />
            <span className="text-xs uppercase tracking-wide text-emerald-100/45">
              {payment.provider}
            </span>
            <span className="ml-auto font-medium text-emerald-50">
              {formatPaise(payment.amount_paise)}
            </span>
          </div>
          {needsPayment && isMock ? (
            <Button
              type="button"
              className="w-full"
              variant="soft"
              disabled={busy}
              onClick={() => void completeMockPayment(payment)}
            >
              {busy ? "Confirming…" : "Simulate successful payment (demo)"}
            </Button>
          ) : null}
          {needsPayment && paymentUrl ? (
            <a
              href={paymentUrl}
              target="_blank"
              rel="noreferrer"
              className="block w-full rounded-xl bg-emerald-500 px-4 py-2.5 text-center text-sm font-semibold text-emerald-950 hover:bg-emerald-400"
            >
              Pay with Cashfree
            </a>
          ) : null}
          {needsPayment && !isMock && !paymentUrl ? (
            <p className="text-xs text-amber-200/70">
              Complete payment in the Cashfree checkout, then return here.
            </p>
          ) : null}
        </div>
      ) : (
        <p className="mt-3 text-sm text-emerald-100/45">No payment record yet.</p>
      )}
      {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
      {needsPayment ? (
        <p className="mt-3 text-xs text-emerald-100/35">Status refreshes every 5 seconds.</p>
      ) : null}
    </section>
  );
}
