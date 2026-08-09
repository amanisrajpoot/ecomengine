"use client";

import { ApiError } from "@commerce/api-client";
import type { LedgerEvent } from "@commerce/types";
import { LedgerBalancesPanel, LedgerEntryCard, Spinner } from "@commerce/ui";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";

import { api, getTenantId, getToken } from "../../../../lib/session";

export default function LedgerEventPage() {
  const router = useRouter();
  const params = useParams<{ eventGroupId: string }>();
  const [event, setEvent] = useState<LedgerEvent | null>(null);
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
        const data = await api().getLedgerEvent(params.eventGroupId);
        if (!cancelled) setEvent(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Ledger event not found");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [params.eventGroupId, router]);

  const balances = useMemo(() => {
    if (!event) return [];
    const buckets = new Map<string, { debit: number; credit: number }>();
    for (const entry of event.entries) {
      const row = buckets.get(entry.account) ?? { debit: 0, credit: 0 };
      if (entry.direction === "DEBIT") row.debit += entry.amount_paise;
      else row.credit += entry.amount_paise;
      buckets.set(entry.account, row);
    }
    return [...buckets.entries()].map(([account, vals]) => ({
      account,
      debit_paise: vals.debit,
      credit_paise: vals.credit,
      net_paise: vals.credit - vals.debit,
    }));
  }, [event]);

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <Link href="/ledger" className="text-sm text-violet-300/70 hover:text-violet-100">
        ← Ledger
      </Link>
      <p className="mt-4 font-display text-4xl text-violet-50">Ledger event</p>
      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-violet-300" />
        </div>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      {event ? (
        <div className="mt-8 space-y-6">
          <div className="rounded-2xl border border-violet-300/20 bg-violet-500/10 px-5 py-4">
            <p className="text-lg font-medium text-violet-50">{event.event_type}</p>
            <p className="mt-1 text-sm text-violet-100/60">{event.reference_key}</p>
            {event.order_id ? (
              <p className="mt-2 text-xs text-violet-100/45">Order {event.order_id}</p>
            ) : null}
          </div>
          <LedgerBalancesPanel balances={balances} className="border-violet-200/15" />
          <ul className="flex flex-col gap-3">
            {event.entries.map((entry) => (
              <li key={entry.id}>
                <LedgerEntryCard entry={entry} />
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </main>
  );
}
