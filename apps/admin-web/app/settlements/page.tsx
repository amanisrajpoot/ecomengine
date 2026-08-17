"use client";

import { useEffect, useState } from "react";

import type { Settlement } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Card, PriceDisplay } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export default function SettlementsPage() {
  const [settlements, setSettlements] = useState<Settlement[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        if (!session.getAccessToken()) {
          setError("Sign in first.");
          return;
        }
        const list = await getApiClient().listSettlements();
        setSettlements(list);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load settlements");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Settlements</h1>
      {loading ? <p className="text-sm text-violet-200/60">Loading…</p> : null}
      {error ? <p className="text-sm text-red-300">{error}</p> : null}

      <ul className="space-y-2">
        {settlements.map((s) => (
          <li key={s.id}>
            <Card>
              <div className="flex justify-between gap-3">
                <div>
                  <p className="font-medium">{s.party_type} · {s.status}</p>
                  <p className="font-mono text-xs text-violet-300/60">{s.id}</p>
                  <p className="text-xs text-violet-200/60">
                    {s.period_start} → {s.period_end}
                  </p>
                </div>
                <PriceDisplay paise={s.total_paise} />
              </div>
            </Card>
          </li>
        ))}
      </ul>

      {!loading && !error && settlements.length === 0 ? (
        <p className="text-sm text-violet-200/60">No settlements in this tenant.</p>
      ) : null}
    </div>
  );
}
