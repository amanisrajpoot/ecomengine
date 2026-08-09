"use client";

import { ApiError } from "@commerce/api-client";
import type { Settlement } from "@commerce/types";
import { Button, SettlementCard, Spinner } from "@commerce/ui";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { JsonBlock } from "../../../components/JsonBlock";
import { api, getTenantId, getToken } from "../../../lib/session";

export default function SettlementDetailPage() {
  const router = useRouter();
  const params = useParams<{ settlementId: string }>();
  const [settlement, setSettlement] = useState<Settlement | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

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
    if (!getTenantId()) {
      setError("Select a tenant on the Tenants page first.");
      setLoading(false);
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

  async function runAction(
    action: "calculate" | "reconcile" | "approve" | "mark-paid",
  ) {
    setBusy(true);
    setError(null);
    try {
      const client = api();
      let updated: Settlement;
      if (action === "calculate") updated = await client.calculateSettlement(params.settlementId);
      else if (action === "reconcile") updated = await client.reconcileSettlement(params.settlementId);
      else if (action === "approve") updated = await client.approveSettlement(params.settlementId);
      else updated = await client.markSettlementPaid(params.settlementId);
      setSettlement(updated);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Action failed");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto flex max-w-3xl justify-center px-5 py-20">
        <Spinner size="lg" className="text-violet-300" />
      </main>
    );
  }

  const status = settlement?.status ?? "";

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <Link href="/settlements" className="text-sm text-violet-100/50 hover:text-violet-50">
        ← Settlements
      </Link>
      <p className="mt-4 font-display text-4xl text-violet-50">Settlement detail</p>
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      {settlement ? (
        <div className="mt-8 space-y-6">
          <SettlementCard settlement={settlement} />

          <div className="flex flex-wrap gap-2">
            {status === "PENDING" ? (
              <Button disabled={busy} onClick={() => void runAction("calculate")}>
                Calculate
              </Button>
            ) : null}
            {status === "CALCULATED" ? (
              <Button disabled={busy} variant="soft" onClick={() => void runAction("reconcile")}>
                Reconcile
              </Button>
            ) : null}
            {status === "RECONCILED" ? (
              <Button disabled={busy} onClick={() => void runAction("approve")}>
                Approve
              </Button>
            ) : null}
            {status === "APPROVED" ? (
              <Button disabled={busy} onClick={() => void runAction("mark-paid")}>
                Mark paid
              </Button>
            ) : null}
          </div>

          <JsonBlock title="Report" data={settlement.report} />
          <JsonBlock title="Ledger entry IDs" data={settlement.ledger_entry_ids} />
        </div>
      ) : null}
    </main>
  );
}
