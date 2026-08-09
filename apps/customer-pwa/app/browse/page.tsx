"use client";

import { ApiError } from "@commerce/api-client";
import type { NearbyStore } from "@commerce/types";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import { api, getToken } from "../../lib/session";

const DEFAULT_LAT = 12.9784;
const DEFAULT_LNG = 77.6408;

function BrowseInner() {
  const router = useRouter();
  const params = useSearchParams();
  const type = params.get("type") ?? undefined;
  const [stores, setStores] = useState<NearbyStore[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      setLoading(true);
      setError(null);
      try {
        const rows = await api().nearbyStores({
          lat: DEFAULT_LAT,
          lng: DEFAULT_LNG,
          radius_km: 8,
          type,
        });
        if (!cancelled) setStores(rows);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load nearby places");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router, type]);

  return (
    <main className="mx-auto max-w-5xl px-5 py-10">
      <p className="font-display text-4xl text-emerald-50">Nearby</p>
      <p className="mt-2 text-sm text-emerald-100/60">
        Searching around Indiranagar demo coordinates
        {type ? ` · ${type}` : " · Food & Grocery"}.
      </p>
      <div className="mt-4 flex flex-wrap gap-2 text-sm">
        {[
          { href: "/browse", label: "All" },
          { href: "/browse?type=FOOD", label: "Food" },
          { href: "/browse?type=GROCERY", label: "Grocery" },
          { href: "/browse?type=RETAIL", label: "Retail" },
        ].map((chip) => (
          <Link
            key={chip.href}
            href={chip.href}
            className="rounded-lg border border-emerald-200/15 px-3 py-1.5 text-emerald-50/80 hover:bg-emerald-400/10"
          >
            {chip.label}
          </Link>
        ))}
      </div>

      {loading ? <p className="mt-8 text-emerald-100/50">Finding places…</p> : null}
      {error ? <p className="mt-8 text-rose-300">{error}</p> : null}

      <ul className="mt-8 grid gap-3">
        {stores.map((store) => (
          <li key={store.location_id}>
            <Link
              href={`/business/${store.business_id}?location=${store.location_id}&type=${store.business_type}`}
              className="block rounded-2xl border border-emerald-200/10 bg-emerald-950/25 px-5 py-4 transition hover:border-emerald-300/25"
            >
              <div className="flex items-baseline justify-between gap-3">
                <p className="font-display text-2xl text-emerald-50">{store.business_name}</p>
                <span className="text-xs uppercase tracking-wide text-emerald-200/50">
                  {store.business_type}
                </span>
              </div>
              <p className="mt-1 text-sm text-emerald-100/55">
                {store.location_name} · {store.distance_km.toFixed(1)} km
              </p>
            </Link>
          </li>
        ))}
      </ul>
      {!loading && !error && stores.length === 0 ? (
        <p className="mt-8 text-emerald-100/55">
          No open locations nearby. Seed food/hyperlocal demos or widen the radius.
        </p>
      ) : null}
    </main>
  );
}

export default function BrowsePage() {
  return (
    <Suspense fallback={<main className="px-5 py-10 text-emerald-100/50">Loading…</main>}>
      <BrowseInner />
    </Suspense>
  );
}
