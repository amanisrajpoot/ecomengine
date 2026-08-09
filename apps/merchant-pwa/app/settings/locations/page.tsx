"use client";

import { ApiError } from "@commerce/api-client";
import type { Business, BusinessLocation } from "@commerce/types";
import { Button, EmptyState, LocationCard, Spinner } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, getBusinessId, getToken, setBusinessId } from "../../../lib/session";

export default function LocationsSettingsPage() {
  const router = useRouter();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(getBusinessId());
  const [locations, setLocations] = useState<BusinessLocation[]>([]);
  const [showInactive, setShowInactive] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const loadLocations = useCallback(async (businessId: string, includeInactive: boolean) => {
    const rows = await api().listLocations(businessId, !includeInactive);
    setLocations(rows);
  }, []);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const rows = await api().listBusinesses();
        if (cancelled) return;
        setBusinesses(rows);
        const current =
          selectedId && rows.some((row) => row.id === selectedId)
            ? selectedId
            : rows[0]?.id ?? null;
        if (current && current !== selectedId) {
          setSelectedId(current);
          setBusinessId(current);
        }
        if (current) await loadLocations(current, showInactive);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load locations");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [loadLocations, router, selectedId, showInactive]);

  async function onBusinessChange(id: string) {
    setSelectedId(id);
    setBusinessId(id);
    setLoading(true);
    setError(null);
    try {
      await loadLocations(id, showInactive);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load locations");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <Link href="/settings" className="text-sm text-amber-100/50 hover:text-amber-50">
        ← Settings
      </Link>
      <div className="mt-4 flex flex-wrap items-end justify-between gap-3">
        <p className="font-display text-4xl text-amber-50">Locations</p>
        {selectedId && !loading ? (
          <Link href="/settings/locations/new">
            <Button variant="soft">Add location</Button>
          </Link>
        ) : null}
      </div>

      <label className="mt-6 flex max-w-md flex-col gap-1.5 text-sm text-amber-50/80">
        <span>Business</span>
        <select
          className="rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
          value={selectedId ?? ""}
          onChange={(e) => void onBusinessChange(e.target.value)}
        >
          {businesses.map((row) => (
            <option key={row.id} value={row.id}>
              {row.name} ({row.type})
            </option>
          ))}
        </select>
      </label>

      <label className="mt-4 flex items-center gap-2 text-sm text-amber-100/70">
        <input
          type="checkbox"
          checked={showInactive}
          onChange={(e) => setShowInactive(e.target.checked)}
          className="rounded border-amber-200/20"
        />
        Show inactive locations
      </label>

      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-amber-300" />
        </div>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      {!loading ? (
        <ul className="mt-8 flex flex-col gap-3">
          {locations.map((location) => (
            <li key={location.id}>
              <LocationCard
                location={location}
                href={`/settings/locations/${location.id}`}
                className="!border-amber-200/10 !bg-amber-950/25 hover:!border-amber-300/25"
              />
            </li>
          ))}
        </ul>
      ) : null}

      {!loading && !error && locations.length === 0 ? (
        <EmptyState
          className="mt-8 border-amber-200/15"
          title="No locations"
          description="Add a store or kitchen location with address and hours."
          action={
            <Link href="/settings/locations/new">
              <Button variant="soft">Add location</Button>
            </Link>
          }
        />
      ) : null}
    </main>
  );
}
