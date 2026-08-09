"use client";

import { ApiError } from "@commerce/api-client";
import type { Business, Settlement } from "@commerce/types";
import { Button, Spinner, TextField } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { defaultSettlementPeriod } from "../../../lib/settlements";
import { api, getTenantId, getToken } from "../../../lib/session";

export default function NewSettlementPage() {
  const router = useRouter();
  const period = defaultSettlementPeriod();
  const [partyType, setPartyType] = useState("MERCHANT");
  const [partyId, setPartyId] = useState("");
  const [periodStart, setPeriodStart] = useState(period.period_start.slice(0, 16));
  const [periodEnd, setPeriodEnd] = useState(period.period_end.slice(0, 16));
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [tenantId, setTenantIdState] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const tid = getTenantId();
    if (!tid) {
      setError("Select a tenant on the Tenants page first.");
      setLoading(false);
      return;
    }
    setTenantIdState(tid);
    let cancelled = false;
    (async () => {
      try {
        const biz = await api().listBusinesses({ status: "ACTIVE" });
        if (!cancelled) {
          setBusinesses(biz);
          setPartyId(biz[0]?.id ?? tid);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load businesses");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router]);

  useEffect(() => {
    if (!tenantId) return;
    if (partyType === "PLATFORM") setPartyId(tenantId);
    else if (partyType === "MERCHANT" && businesses[0]) setPartyId(businesses[0].id);
  }, [businesses, partyType, tenantId]);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    if (!partyId) {
      setError("Party ID is required.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const settlement = await api().createSettlement({
        party_type: partyType,
        party_id: partyId,
        period_start: new Date(periodStart).toISOString(),
        period_end: new Date(periodEnd).toISOString(),
      });
      router.push(`/settlements/${settlement.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create settlement");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto flex max-w-xl justify-center px-5 py-20">
        <Spinner size="lg" className="text-violet-300" />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-xl px-5 py-10">
      <Link href="/settlements" className="text-sm text-violet-100/50 hover:text-violet-50">
        ← Settlements
      </Link>
      <p className="mt-4 font-display text-4xl text-violet-50">New settlement</p>
      <form onSubmit={onSubmit} className="mt-8 flex flex-col gap-4">
        <label className="flex flex-col gap-1.5 text-sm text-violet-50/80">
          <span>Party type</span>
          <select
            className="rounded-xl border border-violet-200/15 bg-violet-950/40 px-3 py-2.5 text-violet-50"
            value={partyType}
            onChange={(e) => setPartyType(e.target.value)}
          >
            {["MERCHANT", "RIDER", "PLATFORM"].map((value) => (
              <option key={value} value={value}>
                {value}
              </option>
            ))}
          </select>
        </label>

        {partyType === "MERCHANT" ? (
          <label className="flex flex-col gap-1.5 text-sm text-violet-50/80">
            <span>Business</span>
            <select
              className="rounded-xl border border-violet-200/15 bg-violet-950/40 px-3 py-2.5 text-violet-50"
              value={partyId}
              onChange={(e) => setPartyId(e.target.value)}
            >
              {businesses.map((business) => (
                <option key={business.id} value={business.id}>
                  {business.name}
                </option>
              ))}
            </select>
          </label>
        ) : partyType === "PLATFORM" ? (
          <p className="text-sm text-violet-100/55">Platform party uses tenant ID: {tenantId}</p>
        ) : (
          <TextField
            label="Rider party ID"
            value={partyId}
            onChange={(e) => setPartyId(e.target.value)}
            placeholder="Delivery partner profile UUID"
            required
          />
        )}

        <TextField
          label="Period start"
          type="datetime-local"
          value={periodStart}
          onChange={(e) => setPeriodStart(e.target.value)}
          required
        />
        <TextField
          label="Period end"
          type="datetime-local"
          value={periodEnd}
          onChange={(e) => setPeriodEnd(e.target.value)}
          required
        />

        {error ? <p className="text-rose-300">{error}</p> : null}
        <Button type="submit" disabled={busy}>
          {busy ? "Creating…" : "Create settlement"}
        </Button>
      </form>
    </main>
  );
}
