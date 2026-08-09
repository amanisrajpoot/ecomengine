"use client";

import { ApiError } from "@commerce/api-client";
import type { Business, Settlement } from "@commerce/types";
import { EmptyState, SettlementCard, Spinner } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, getBusinessId, getToken, setBusinessId } from "../../lib/session";

export default function MerchantSettlementsPage() {
  const router = useRouter();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selected, setSelected] = useState<string | null>(getBusinessId());
  const [settlements, setSettlements] = useState<Settlement[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (businessId: string) => {
    const rows = await api().listSettlements({
      party_type: "MERCHANT",
      party_id: businessId,
    });
    setSettlements(rows);
  }, []);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const biz = await api().listBusinesses({ status: "ACTIVE" });
        if (cancelled) return;
        setBusinesses(biz);
        const current = selected ?? biz[0]?.id ?? null;
        if (current && !selected) {
          setSelected(current);
          setBusinessId(current);
        }
        if (current) await load(current);
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
  }, [load, router, selected]);

  async function onBusinessChange(id: string) {
    setSelected(id);
    setBusinessId(id);
    setLoading(true);
    setError(null);
    try {
      await load(id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load settlements");
    } finally {
      setLoading(false);
    }
  }

  const selectedBusiness = businesses.find((b) => b.id === selected);

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <p className="font-display text-4xl text-amber-50">Settlements</p>
      <p className="mt-2 text-sm text-amber-100/55">
        Payout periods for your business. Admin approves and marks paid.
      </p>

      <label className="mt-6 flex flex-col gap-1.5 text-sm text-amber-50/80">
        <span>Business</span>
        <select
          className="rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
          value={selected ?? ""}
          onChange={(e) => onBusinessChange(e.target.value)}
        >
          {businesses.map((b) => (
            <option key={b.id} value={b.id}>
              {b.name} ({b.type})
            </option>
          ))}
        </select>
      </label>

      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-amber-300" />
        </div>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      <ul className="mt-8 flex flex-col gap-3">
        {settlements.map((settlement) => (
          <li key={settlement.id}>
            <Link href={`/settlements/${settlement.id}`}>
              <SettlementCard
                settlement={settlement}
                partyLabel={selectedBusiness?.name}
                className="!border-amber-200/10 !bg-amber-950/25 hover:!border-amber-300/25"
              />
            </Link>
          </li>
        ))}
      </ul>

      {!loading && !error && settlements.length === 0 ? (
        <EmptyState
          className="mt-8 border-amber-200/15"
          title="No settlements yet"
          description="After delivered COD orders, an admin creates and calculates settlement periods."
        />
      ) : null}
    </main>
  );
}
