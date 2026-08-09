"use client";

import { ApiError } from "@commerce/api-client";
import type { Settlement } from "@commerce/types";
import { SettlementCard, Spinner } from "@commerce/ui";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, getToken } from "../../../lib/session";

export default function RiderSettlementDetailPage() {
  const router = useRouter();
  const params = useParams<{ settlementId: string }>();
  const [settlement, setSettlement] = useState<Settlement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const data = await api().getSettlement(params.settlementId);
    setSettlement(data);
    return data;
  }, [params.settlementId]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        await load();
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Settlement not found");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [load, router]);

  if (loading) {
    return (
      <main className="mx-auto flex max-w-xl justify-center px-5 py-20">
        <Spinner size="lg" className="text-sky-300" />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-xl px-5 py-10">
      <Link href="/settlements" className="text-sm text-sky-100/50 hover:text-sky-50">
        ← Earnings
      </Link>
      <p className="mt-4 font-display text-4xl text-sky-50">Payout</p>
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      {settlement ? (
        <div className="mt-8 space-y-6">
          <SettlementCard
            settlement={settlement}
            className="!border-sky-200/10 !bg-sky-950/25"
          />
          <section className="rounded-2xl border border-sky-200/10 px-4 py-4 text-sm text-sky-100/70">
            <p className="font-medium text-sky-50/90">Report summary</p>
            <pre className="mt-3 overflow-x-auto text-xs text-sky-100/55">
              {JSON.stringify(settlement.report, null, 2)}
            </pre>
          </section>
          <p className="text-xs text-sky-100/40">
            {settlement.ledger_entry_ids.length} ledger entries linked.
          </p>
        </div>
      ) : null}
    </main>
  );
}
