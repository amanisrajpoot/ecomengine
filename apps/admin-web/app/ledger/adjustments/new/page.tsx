"use client";

import { ApiError } from "@commerce/api-client";
import type { LedgerEvent } from "@commerce/types";
import { Button, Spinner, TextField } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { api, getTenantId, getToken } from "../../../../lib/session";

const ACCOUNTS = [
  "PLATFORM_CASH",
  "CUSTOMER_RECEIVABLE",
  "TAX_LIABILITY",
  "PLATFORM_FEE_REVENUE",
  "PLATFORM_COMMISSION",
  "MERCHANT_PAYABLE",
  "RIDER_PAYABLE",
  "PLATFORM_CLEARING",
];

type LineDraft = {
  account: string;
  direction: "DEBIT" | "CREDIT";
  amount_paise: string;
};

const emptyLine = (): LineDraft => ({
  account: "MERCHANT_PAYABLE",
  direction: "DEBIT",
  amount_paise: "",
});

export default function NewLedgerAdjustmentPage() {
  const router = useRouter();
  const [referenceKey, setReferenceKey] = useState("");
  const [orderId, setOrderId] = useState("");
  const [reason, setReason] = useState("");
  const [lines, setLines] = useState<LineDraft[]>([emptyLine(), { ...emptyLine(), direction: "CREDIT" }]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    if (!getTenantId()) {
      setError("Select a tenant on the Tenants page first.");
    }
    setLoading(false);
  }, [router]);

  function updateLine(index: number, patch: Partial<LineDraft>) {
    setLines((prev) => prev.map((line, i) => (i === index ? { ...line, ...patch } : line)));
  }

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!referenceKey.trim()) {
      setError("Reference key is required.");
      return;
    }
    const parsed = lines.map((line) => ({
      account: line.account,
      direction: line.direction,
      amount_paise: Number.parseInt(line.amount_paise, 10),
    }));
    if (parsed.some((line) => !line.amount_paise || line.amount_paise <= 0)) {
      setError("Each line needs a positive amount in paise.");
      return;
    }
    const debits = parsed
      .filter((line) => line.direction === "DEBIT")
      .reduce((sum, line) => sum + line.amount_paise, 0);
    const credits = parsed
      .filter((line) => line.direction === "CREDIT")
      .reduce((sum, line) => sum + line.amount_paise, 0);
    if (debits !== credits) {
      setError(`Unbalanced posting: debits ${debits} vs credits ${credits} paise.`);
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const eventRead: LedgerEvent = await api().createLedgerAdjustment({
        reference_key: referenceKey.trim(),
        order_id: orderId.trim() || undefined,
        reason: reason.trim() || undefined,
        lines: parsed,
      });
      router.push(`/ledger/events/${eventRead.event_group_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Adjustment failed");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto flex max-w-xl justify-center px-5 py-20">
        <Spinner size="lg" className="text-violet-300" />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-xl px-5 py-10">
      <Link href="/ledger" className="text-sm text-violet-300/70 hover:text-violet-100">
        ← Ledger
      </Link>
      <p className="mt-4 font-display text-4xl text-violet-50">Manual adjustment</p>
      <p className="mt-2 text-sm text-violet-100/55">
        Post a balanced multi-line correction. Debits must equal credits.
      </p>

      <form className="mt-8 space-y-5" onSubmit={(e) => void onSubmit(e)}>
        <TextField
          label="Reference key"
          value={referenceKey}
          onChange={(e) => setReferenceKey(e.target.value)}
          placeholder="manual-correction-001"
          className="!border-violet-200/15 !bg-violet-950/40 !text-violet-50"
        />
        <TextField
          label="Order ID (optional)"
          value={orderId}
          onChange={(e) => setOrderId(e.target.value)}
          placeholder="UUID"
          className="!border-violet-200/15 !bg-violet-950/40 !text-violet-50"
        />
        <TextField
          label="Reason"
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Describe the correction"
          className="!border-violet-200/15 !bg-violet-950/40 !text-violet-50"
        />

        <div className="space-y-3">
          <p className="text-sm text-violet-50/80">Lines</p>
          {lines.map((line, index) => (
            <div
              key={index}
              className="grid gap-2 rounded-xl border border-violet-200/10 bg-violet-950/20 p-3 sm:grid-cols-4"
            >
              <select
                className="rounded-lg border border-violet-200/15 bg-violet-950/40 px-2 py-2 text-sm text-violet-50"
                value={line.account}
                onChange={(e) => updateLine(index, { account: e.target.value })}
              >
                {ACCOUNTS.map((account) => (
                  <option key={account} value={account}>
                    {account}
                  </option>
                ))}
              </select>
              <select
                className="rounded-lg border border-violet-200/15 bg-violet-950/40 px-2 py-2 text-sm text-violet-50"
                value={line.direction}
                onChange={(e) =>
                  updateLine(index, { direction: e.target.value as LineDraft["direction"] })
                }
              >
                <option value="DEBIT">DEBIT</option>
                <option value="CREDIT">CREDIT</option>
              </select>
              <input
                type="number"
                min={1}
                className="rounded-lg border border-violet-200/15 bg-violet-950/40 px-2 py-2 text-sm text-violet-50 sm:col-span-2"
                placeholder="Amount (paise)"
                value={line.amount_paise}
                onChange={(e) => updateLine(index, { amount_paise: e.target.value })}
              />
            </div>
          ))}
          <button
            type="button"
            className="text-sm text-violet-300 hover:text-violet-100"
            onClick={() => setLines((prev) => [...prev, emptyLine()])}
          >
            + Add line
          </button>
        </div>

        {error ? <p className="text-rose-300">{error}</p> : null}

        <Button
          type="submit"
          disabled={busy}
          className="w-full !bg-violet-500 !text-violet-50 hover:!bg-violet-400"
        >
          {busy ? "Posting…" : "Post adjustment"}
        </Button>
      </form>
    </main>
  );
}
