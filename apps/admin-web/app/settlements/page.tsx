"use client";

import { ApiError } from "@commerce/api-client";
import type { Settlement } from "@commerce/types";
import { EmptyState, SettlementCard, Spinner } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, getTenantId, getToken } from "../../lib/session";

export default function SettlementsPage() {
  const router = useRouter();
  const [settlements, setSettlements] = useState<Settlement[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [partyType, setPartyType] = useState("");
  const [status, setStatus] = useState("");

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
        const rows = await api().listSettlements({
          party_type: partyType || undefined,
          status: status || undefined,
        });
        if (!cancelled) setSettlements(rows);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load settlements");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [partyType, router, status]);

  return (
    <main className="mx-auto max-w-5xl px-5 py-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <p className="font-display text-4xl text-violet-50">Settlements</p>
        <Link
          href="/settlements/new"
          className="rounded-xl bg-violet-500 px-4 py-2 text-sm font-semibold text-violet-50 hover:bg-violet-400"
        >
          New settlement
        </Link>
      </div>
      <p className="mt-2 text-sm text-violet-100/55">
        Ledger aggregation → calculate → reconcile → approve → mark paid.
      </p>

      <div className="mt-6 grid gap-4 sm:grid-cols-2">
        <label className="flex flex-col gap-1.5 text-sm text-violet-50/80">
          <span>Party type</span>
          <select
            className="rounded-xl border border-violet-200/15 bg-violet-950/40 px-3 py-2.5 text-violet-50"
            value={partyType}
            onChange={(e) => setPartyType(e.target.value)}
          >
            <option value="">All</option>
            {["MERCHANT", "RIDER", "PLATFORM"].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
        <label className="flex flex-col gap-1.5 text-sm text-violet-50/80">
          <span>Status</span>
          <select
            className="rounded-xl border border-violet-200/15 bg-violet-950/40 px-3 py-2.5 text-violet-50"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="">All</option>
            {["PENDING", "CALCULATED", "RECONCILED", "APPROVED", "PAID"].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>
      </div>

      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-violet-300" />
        </div>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      <ul className="mt-8 flex flex-col gap-3">
        {settlements.map((settlement) => (
          <li key={settlement.id}>
            <Link href={`/settlements/${settlement.id}`}>
              <SettlementCard settlement={settlement} className="hover:border-violet-300/25" />
            </Link>
          </li>
        ))}
      </ul>

      {!loading && !error && settlements.length === 0 ? (
        <EmptyState
          className="mt-8 border-violet-200/15"
          title="No settlements"
          description="Create a settlement period and run calculate after orders generate ledger entries."
        />
      ) : null}
    </main>
  );
}
