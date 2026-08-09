"use client";

import { ApiError } from "@commerce/api-client";
import type { Partner, Settlement } from "@commerce/types";
import { EmptyState, SettlementCard, Spinner } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, getToken } from "../../lib/session";

export default function RiderSettlementsPage() {
  const router = useRouter();
  const [partner, setPartner] = useState<Partner | null>(null);
  const [settlements, setSettlements] = useState<Settlement[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (partnerId: string) => {
    const rows = await api().listSettlements({
      party_type: "RIDER",
      party_id: partnerId,
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
        const me = await api().getMyPartner();
        if (cancelled) return;
        setPartner(me);
        await load(me.id);
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
  }, [load, router]);

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <p className="font-display text-4xl text-sky-50">Earnings</p>
      <p className="mt-2 text-sm text-sky-100/55">
        Payout periods for {partner?.display_name ?? "your rider profile"}. Admin approves and
        marks paid.
      </p>

      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-sky-300" />
        </div>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      <ul className="mt-8 flex flex-col gap-3">
        {settlements.map((settlement) => (
          <li key={settlement.id}>
            <Link href={`/settlements/${settlement.id}`}>
              <SettlementCard
                settlement={settlement}
                partyLabel={partner?.display_name ?? "Rider"}
                className="!border-sky-200/10 !bg-sky-950/25 hover:!border-sky-300/25"
              />
            </Link>
          </li>
        ))}
      </ul>

      {!loading && !error && settlements.length === 0 ? (
        <EmptyState
          className="mt-8 border-sky-200/15"
          title="No payouts yet"
          description="After delivered jobs, an admin creates and calculates RIDER settlement periods."
        />
      ) : null}
    </main>
  );
}
