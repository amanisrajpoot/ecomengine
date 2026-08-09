"use client";

import { ApiError } from "@commerce/api-client";
import type { Business, BusinessLocation, InventoryItem } from "@commerce/types";
import { Button, EmptyState, Spinner } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import {
  businessHasInventory,
  loadVariantLabels,
  variantDisplay,
  type VariantLabel,
} from "../../lib/inventory-helpers";
import {
  api,
  getBusinessId,
  getLocationId,
  getToken,
  setBusinessId,
  setLocationId,
} from "../../lib/session";

const POLL_MS = 10000;
type StockFilter = "all" | "low" | "out";

function stockBadge(item: InventoryItem) {
  if (item.is_out_of_stock) {
    return (
      <span className="rounded-full bg-rose-500/15 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-rose-300">
        Out of stock
      </span>
    );
  }
  if (item.is_low_stock) {
    return (
      <span className="rounded-full bg-amber-500/15 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-amber-200">
        Low stock
      </span>
    );
  }
  return (
    <span className="rounded-full bg-emerald-500/15 px-2 py-0.5 text-[10px] font-medium uppercase tracking-wide text-emerald-200">
      In stock
    </span>
  );
}

export default function InventoryPage() {
  const router = useRouter();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [locations, setLocations] = useState<BusinessLocation[]>([]);
  const [selectedBusiness, setSelectedBusiness] = useState<string | null>(getBusinessId());
  const [selectedLocation, setSelectedLocation] = useState<string | null>(getLocationId());
  const [filter, setFilter] = useState<StockFilter>("all");
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [labels, setLabels] = useState<Map<string, VariantLabel>>(new Map());
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const inventoryBusinesses = useMemo(
    () => businesses.filter((b) => businessHasInventory(b.capabilities)),
    [businesses],
  );

  const loadInventory = useCallback(
    async (businessId: string, locationId: string | null, stockFilter: StockFilter) => {
      const rows = await api().listInventory(businessId, {
        location_id: locationId ?? undefined,
        low_stock_only: stockFilter === "low",
        out_of_stock_only: stockFilter === "out",
      });
      setItems(rows);
      const variantLabels = await loadVariantLabels(api(), businessId);
      setLabels(variantLabels);
    },
    [],
  );

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
        const capable = biz.filter((b) => businessHasInventory(b.capabilities));
        const current =
          selectedBusiness && capable.some((b) => b.id === selectedBusiness)
            ? selectedBusiness
            : capable[0]?.id ?? null;
        if (current && current !== selectedBusiness) {
          setSelectedBusiness(current);
          setBusinessId(current);
        }
        if (!current) {
          setLoading(false);
          return;
        }
        const locs = await api().listLocations(current);
        if (cancelled) return;
        setLocations(locs);
        const loc =
          selectedLocation && locs.some((l) => l.id === selectedLocation)
            ? selectedLocation
            : locs[0]?.id ?? null;
        if (loc !== selectedLocation) {
          setSelectedLocation(loc);
          setLocationId(loc);
        }
        await loadInventory(current, loc, filter);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load inventory");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [filter, loadInventory, router, selectedBusiness, selectedLocation]);

  useEffect(() => {
    if (!selectedBusiness || loading) return;
    const timer = window.setInterval(() => {
      loadInventory(selectedBusiness, selectedLocation, filter).catch(() => undefined);
    }, POLL_MS);
    return () => window.clearInterval(timer);
  }, [filter, loadInventory, loading, selectedBusiness, selectedLocation]);

  async function onBusinessChange(id: string) {
    setSelectedBusiness(id);
    setBusinessId(id);
    setLoading(true);
    setError(null);
    try {
      const locs = await api().listLocations(id);
      setLocations(locs);
      const loc = locs[0]?.id ?? null;
      setSelectedLocation(loc);
      setLocationId(loc);
      await loadInventory(id, loc, filter);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load inventory");
    } finally {
      setLoading(false);
    }
  }

  async function onLocationChange(id: string) {
    if (!selectedBusiness) return;
    setSelectedLocation(id);
    setLocationId(id);
    setLoading(true);
    setError(null);
    try {
      await loadInventory(selectedBusiness, id, filter);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load inventory");
    } finally {
      setLoading(false);
    }
  }

  async function onFilterChange(next: StockFilter) {
    if (!selectedBusiness) return;
    setFilter(next);
    setLoading(true);
    setError(null);
    try {
      await loadInventory(selectedBusiness, selectedLocation, next);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load inventory");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <p className="font-display text-4xl text-amber-50">Stock board</p>
        {selectedBusiness && !loading ? (
          <Link href="/inventory/new">
            <Button variant="soft">Add stock item</Button>
          </Link>
        ) : null}
      </div>

      {inventoryBusinesses.length === 0 && !loading ? (
        <EmptyState
          className="mt-8 border-amber-200/15"
          title="Inventory not enabled"
          description="Select a grocery or retail business with inventory capability."
        />
      ) : (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <label className="flex flex-col gap-1.5 text-sm text-amber-50/80">
              <span>Business</span>
              <select
                className="rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
                value={selectedBusiness ?? ""}
                onChange={(e) => onBusinessChange(e.target.value)}
              >
                {inventoryBusinesses.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name} ({b.type})
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1.5 text-sm text-amber-50/80">
              <span>Location</span>
              <select
                className="rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
                value={selectedLocation ?? ""}
                onChange={(e) => onLocationChange(e.target.value)}
              >
                {locations.map((loc) => (
                  <option key={loc.id} value={loc.id}>
                    {loc.name}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="mt-4 flex flex-wrap gap-2">
            {(
              [
                ["all", "All"],
                ["low", "Low stock"],
                ["out", "Out of stock"],
              ] as const
            ).map(([value, label]) => (
              <button
                key={value}
                type="button"
                className={`rounded-lg px-3 py-1.5 text-xs font-medium transition ${
                  filter === value
                    ? "bg-amber-400/20 text-amber-50"
                    : "text-amber-100/50 hover:text-amber-50"
                }`}
                onClick={() => void onFilterChange(value)}
              >
                {label}
              </button>
            ))}
          </div>
        </>
      )}

      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-amber-300" />
        </div>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      {!loading && inventoryBusinesses.length > 0 ? (
        <ul className="mt-8 flex flex-col gap-3">
          {items.map((item) => {
            const label = labels.get(item.variant_id);
            return (
              <li key={item.id}>
                <Link
                  href={`/inventory/${item.id}`}
                  className="block rounded-2xl border border-amber-200/10 bg-amber-950/25 px-4 py-4 transition hover:border-amber-300/25"
                >
                  <div className="flex items-start justify-between gap-3">
                    <div>
                      <p className="font-medium text-amber-50">
                        {variantDisplay(label, item.variant_id)}
                      </p>
                      {label?.sku ? (
                        <p className="mt-1 text-xs text-amber-100/45">SKU {label.sku}</p>
                      ) : null}
                    </div>
                    {stockBadge(item)}
                  </div>
                  <div className="mt-3 flex flex-wrap gap-4 text-sm text-amber-100/70">
                    <span>
                      Available <strong className="text-amber-50">{item.available}</strong>
                    </span>
                    <span>
                      On hand <strong className="text-amber-50">{item.on_hand}</strong>
                    </span>
                    <span>
                      Reserved <strong className="text-amber-50">{item.reserved}</strong>
                    </span>
                  </div>
                </Link>
              </li>
            );
          })}
        </ul>
      ) : null}

      {!loading && !error && inventoryBusinesses.length > 0 && items.length === 0 ? (
        <EmptyState
          className="mt-8 border-amber-200/15"
          title="No stock items"
          description="Link a catalog variant to this location to start tracking inventory."
          action={
            <Link href="/inventory/new">
              <Button variant="soft">Add stock item</Button>
            </Link>
          }
        />
      ) : null}

      {selectedBusiness && !loading ? (
        <p className="mt-6 text-xs text-amber-100/40">Auto-refresh every {POLL_MS / 1000}s</p>
      ) : null}
    </main>
  );
}
