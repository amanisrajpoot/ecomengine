"use client";

import type { AccountBalance } from "@commerce/types";
import { formatPaise } from "@commerce/ui";

type LedgerBalancesPanelProps = {
  balances: AccountBalance[];
  className?: string;
  emptyMessage?: string;
};

export function LedgerBalancesPanel({
  balances,
  className = "",
  emptyMessage = "No ledger balances yet.",
}: LedgerBalancesPanelProps) {
  return (
    <section
      className={`rounded-2xl border border-white/10 bg-black/20 px-4 py-4 ${className}`}
    >
      <p className="text-sm font-medium text-white/80">Account balances</p>
      {balances.length === 0 ? (
        <p className="mt-3 text-sm text-white/45">{emptyMessage}</p>
      ) : (
        <div className="mt-3 overflow-x-auto">
          <table className="w-full min-w-[28rem] text-left text-sm">
            <thead>
              <tr className="text-xs uppercase tracking-wide text-white/40">
                <th className="pb-2 pr-3 font-medium">Account</th>
                <th className="pb-2 pr-3 font-medium">Debit</th>
                <th className="pb-2 pr-3 font-medium">Credit</th>
                <th className="pb-2 font-medium">Net</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-white/5">
              {balances.map((row) => (
                <tr key={row.account}>
                  <td className="py-2 pr-3 text-white/75">{row.account}</td>
                  <td className="py-2 pr-3 text-white/55">{formatPaise(row.debit_paise)}</td>
                  <td className="py-2 pr-3 text-white/55">{formatPaise(row.credit_paise)}</td>
                  <td className="py-2 text-white">{formatPaise(row.net_paise)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
