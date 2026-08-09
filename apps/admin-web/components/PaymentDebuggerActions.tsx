"use client";

import { ApiError } from "@commerce/api-client";
import type { Payment } from "@commerce/types";
import { Button, formatPaise } from "@commerce/ui";
import { useState } from "react";

import { api } from "../lib/session";

type PaymentDebuggerActionsProps = {
  orderId: string;
  payments: Record<string, unknown>[];
  onRefresh: () => void;
};

function asPayment(row: Record<string, unknown>): Payment | null {
  if (typeof row.id !== "string" || typeof row.status !== "string") return null;
  return row as unknown as Payment;
}

export function PaymentDebuggerActions({
  orderId,
  payments,
  onRefresh,
}: PaymentDebuggerActionsProps) {
  const [busy, setBusy] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const parsed = payments.map(asPayment).filter((p): p is Payment => p !== null);

  if (!parsed.length) return null;

  async function verify(payment: Payment) {
    setBusy(payment.id);
    setError(null);
    try {
      await api().verifyOrderPayment(orderId, {
        provider: payment.provider,
        provider_ref: payment.provider_ref ?? undefined,
      });
      onRefresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Verify failed");
    } finally {
      setBusy(null);
    }
  }

  async function refund(payment: Payment) {
    setBusy(payment.id);
    setError(null);
    try {
      await api().refundPayment(payment.id, {
        amount_paise: payment.amount_paise,
        reason: "admin_refund",
      });
      onRefresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Refund failed");
    } finally {
      setBusy(null);
    }
  }

  return (
    <section className="rounded-2xl border border-violet-200/10 bg-violet-950/20 px-4 py-4">
      <p className="text-sm font-medium text-violet-50/90">Payment actions</p>
      <ul className="mt-3 space-y-3">
        {parsed.map((payment) => (
          <li
            key={payment.id}
            className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-violet-200/10 px-3 py-3 text-sm"
          >
            <div>
              <p className="text-violet-50">
                {payment.provider} · {payment.status}
              </p>
              <p className="text-xs text-violet-100/50">
                {formatPaise(payment.amount_paise)} · {payment.id.slice(0, 8)}…
              </p>
            </div>
            <div className="flex flex-wrap gap-2">
              {payment.status === "PENDING" ? (
                <Button
                  type="button"
                  variant="soft"
                  disabled={busy === payment.id}
                  onClick={() => void verify(payment)}
                >
                  Verify capture
                </Button>
              ) : null}
              {payment.status === "CAPTURED" ? (
                <Button
                  type="button"
                  variant="ghost"
                  disabled={busy === payment.id}
                  onClick={() => void refund(payment)}
                >
                  Full refund
                </Button>
              ) : null}
            </div>
          </li>
        ))}
      </ul>
      {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
    </section>
  );
}
