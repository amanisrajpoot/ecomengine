"use client";

import { ApiError } from "@commerce/api-client";
import type { Partner } from "@commerce/types";
import { Button, EmptyState, LiveIndicator, PartnerCard, Spinner } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, getTenantId, getToken } from "../../lib/session";

export default function FleetPage() {
  const router = useRouter();
  const [partners, setPartners] = useState<Partner[]>([]);
  const [onlineOnly, setOnlineOnly] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    const rows = await api().listDeliveryPartners({
      online_only: onlineOnly,
      status: "ACTIVE",
    });
    setPartners(rows);
  }, [onlineOnly]);

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
          setError(err instanceof ApiError ? err.message : "Failed to load fleet");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    const timer = window.setInterval(() => {
      load().catch(() => undefined);
    }, 15000);
    return () => {
      cancelled = true;
      window.clearInterval(timer);
    };
  }, [load, router]);

  async function onFilterChange(next: boolean) {
    setOnlineOnly(next);
    setLoading(true);
    setError(null);
    try {
      const rows = await api().listDeliveryPartners({
        online_only: next,
        status: "ACTIVE",
      });
      setPartners(rows);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load fleet");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-5xl px-5 py-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p className="font-display text-4xl text-violet-50">Fleet</p>
          <p className="mt-2 text-sm text-violet-100/55">
            Delivery partners, online status, and vehicles.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <LiveIndicator />
          <Link href="/fleet/new">
            <Button variant="soft">Add partner</Button>
          </Link>
        </div>
      </div>

      <label className="mt-6 flex items-center gap-2 text-sm text-violet-100/70">
        <input
          type="checkbox"
          checked={onlineOnly}
          onChange={(e) => void onFilterChange(e.target.checked)}
          className="rounded border-violet-200/20"
        />
        Online riders only
      </label>

      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-violet-300" />
        </div>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      {!loading ? (
        <ul className="mt-8 flex flex-col gap-3">
          {partners.map((partner) => (
            <li key={partner.id}>
              <PartnerCard
                partner={partner}
                href={`/fleet/${partner.id}`}
                subtitle={`User ${partner.user_id.slice(0, 8)}…`}
                className="!border-violet-200/10 !bg-violet-950/25 hover:!border-violet-300/25"
              />
            </li>
          ))}
        </ul>
      ) : null}

      {!loading && !error && partners.length === 0 ? (
        <EmptyState
          className="mt-8 border-violet-200/15"
          title="No riders"
          description="Link a user as a delivery partner or ask riders to go online in the Rider app."
          action={
            <Link href="/fleet/new">
              <Button variant="soft">Add partner</Button>
            </Link>
          }
        />
      ) : null}
    </main>
  );
}
