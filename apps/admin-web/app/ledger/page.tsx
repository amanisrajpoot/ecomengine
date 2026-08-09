"use client";

import { ApiError } from "@commerce/api-client";
import type { AccountBalance, LedgerEntry } from "@commerce/types";
import {
  EmptyState,
  LedgerBalancesPanel,
  LedgerEntryCard,
  Spinner,
} from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, getTenantId, getToken } from "../../lib/session";

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

const EVENT_TYPES = ["ORDER_PAYMENT_CAPTURED", "PAYMENT_REFUND", "MANUAL_ADJUSTMENT"];

export default function LedgerPage() {
  const router = useRouter();
  const [entries, setEntries] = useState<LedgerEntry[]>([]);
  const [balances, setBalances] = useState<AccountBalance[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [account, setAccount] = useState("");
  const [eventType, setEventType] = useState("");
  const [orderFilter, setOrderFilter] = useState("");

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
        const [rows, balanceRows] = await Promise.all([
          client.listLedgerEntries({
            account: account || undefined,
            event_type: eventType || undefined,
            order_id: orderFilter.trim() || undefined,
          }),
          client.listLedgerBalances(),
        ]);
        if (!cancelled) {
          setEntries(rows);
          setBalances(balanceRows);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load ledger");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [account, eventType, orderFilter, router]);

  return (
    <main className="mx-auto max-w-5xl px-5 py-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <p className="font-display text-4xl text-violet-50">Ledger</p>
        <Link
          href="/ledger/adjustments/new"
          className="rounded-xl bg-violet-500 px-4 py-2 text-sm font-semibold text-violet-50 hover:bg-violet-400"
        >
          Manual adjustment
        </Link>
      </div>
      <p className="mt-2 text-sm text-violet-100/55">
        Immutable financial postings — payment capture, refunds, and adjustments.
      </p>

      <div className="mt-6 grid gap-4 sm:grid-cols-3">
        <label className="flex flex-col gap-1.5 text-sm text-violet-50/80">
          <span>Account</span>
          <select
            className="rounded-xl border border-violet-200/15 bg-violet-950/40 px-3 py-2.5 text-violet-50"
            value={account}
            onChange={(e) => {
              setLoading(true);
              setAccount(e.target.value);
            }}
          >
            <option value="">All</option>
            {ACCOUNTS.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1.5 text-sm text-violet-50/80">
          <span>Event type</span>
          <select
            className="rounded-xl border border-violet-200/15 bg-violet-950/40 px-3 py-2.5 text-violet-50"
            value={eventType}
            onChange={(e) => {
              setLoading(true);
              setEventType(e.target.value);
            }}
          >
            <option value="">All</option>
            {EVENT_TYPES.map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1.5 text-sm text-violet-50/80">
          <span>Order ID</span>
          <input
            type="text"
            className="rounded-xl border border-violet-200/15 bg-violet-950/40 px-3 py-2.5 text-violet-50 placeholder:text-violet-100/30"
            placeholder="Optional UUID"
            value={orderFilter}
            onChange={(e) => {
              setLoading(true);
              setOrderFilter(e.target.value);
            }}
          />
        </label>
      </div>

      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-violet-300" />
        </div>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      <LedgerBalancesPanel balances={balances} className="mt-8 border-violet-200/15" />

      <ul className="mt-8 flex flex-col gap-3">
        {entries.map((entry) => (
          <li key={entry.id}>
            <LedgerEntryCard
              entry={entry}
              eventHref={`/ledger/events/${entry.event_group_id}`}
            />
          </li>
        ))}
      </ul>

      {!loading && !error && entries.length === 0 ? (
        <EmptyState
          className="mt-8 border-violet-200/15"
          title="No ledger entries"
          description="Place and pay for an order to generate payment-captured postings."
        />
      ) : null}
    </main>
  );
}
