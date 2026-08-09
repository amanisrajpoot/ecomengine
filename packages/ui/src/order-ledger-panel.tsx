"use client";

import { ApiError } from "@commerce/api-client";
import type { AccountBalance, LedgerEntry } from "@commerce/types";
import { LedgerBalancesPanel, LedgerEntryCard, Spinner } from "@commerce/ui";
import { useCallback, useEffect, useMemo, useState } from "react";

type OrderLedgerPanelProps = {
  orderId: string;
  loadLedger: (orderId: string) => Promise<LedgerEntry[]>;
  loadBalances?: (orderId: string) => Promise<AccountBalance[]>;
  eventHrefBase?: string;
  className?: string;
  emptyMessage?: string;
};

export function OrderLedgerPanel({
  orderId,
  loadLedger,
  loadBalances,
  eventHrefBase,
  className = "",
  emptyMessage = "No ledger entries for this order yet.",
}: OrderLedgerPanelProps) {
  const [entries, setEntries] = useState<LedgerEntry[]>([]);
  const [balances, setBalances] = useState<AccountBalance[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const rows = await loadLedger(orderId);
    setEntries(rows);
    if (loadBalances) {
      const balanceRows = await loadBalances(orderId);
      setBalances(balanceRows);
    }
    return rows;
  }, [loadBalances, loadLedger, orderId]);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        await load();
        if (!cancelled) setError(null);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Could not load ledger");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [load]);

  const grouped = useMemo(() => {
    const map = new Map<string, LedgerEntry[]>();
    for (const entry of entries) {
      const group = map.get(entry.event_group_id) ?? [];
      group.push(entry);
      map.set(entry.event_group_id, group);
    }
    return [...map.entries()];
  }, [entries]);

  return (
    <section
      className={`rounded-2xl border border-white/10 bg-black/20 px-4 py-4 ${className}`}
    >
      <p className="text-sm font-medium text-white/80">Ledger</p>
      {loading ? (
        <div className="mt-4 flex justify-center">
          <Spinner size="sm" />
        </div>
      ) : entries.length === 0 ? (
        <p className="mt-3 text-sm text-white/45">{emptyMessage}</p>
      ) : (
        <ul className="mt-3 flex flex-col gap-4">
          {grouped.map(([eventGroupId, rows]) => (
            <li key={eventGroupId}>
              <p className="mb-2 text-xs uppercase tracking-wide text-white/40">
                {rows[0]?.event_type ?? "Event"}
              </p>
              <ul className="flex flex-col gap-2">
                {rows.map((entry) => (
                  <li key={entry.id}>
                    <LedgerEntryCard
                      entry={entry}
                      eventHref={
                        eventHrefBase ? `${eventHrefBase}/${entry.event_group_id}` : undefined
                      }
                      className="!border-white/5 !bg-black/10"
                    />
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}
      {loadBalances && balances.length > 0 ? (
        <LedgerBalancesPanel
          balances={balances}
          className="mt-4 !border-white/5 !bg-black/10"
        />
      ) : null}
      {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
    </section>
  );
}
