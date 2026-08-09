"use client";

import { ApiError } from "@commerce/api-client";
import type { BusinessLocation, Product, Variant } from "@commerce/types";
import { Button, Spinner, TextField } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { businessHasInventory } from "../../../lib/inventory-helpers";
import { api, getBusinessId, getLocationId, getToken, setBusinessId } from "../../../lib/session";

export default function NewInventoryItemPage() {
  const router = useRouter();
  const [locations, setLocations] = useState<BusinessLocation[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [variants, setVariants] = useState<Variant[]>([]);
  const [businessId, setSelectedBusiness] = useState<string | null>(getBusinessId());
  const [locationId, setSelectedLocation] = useState<string | null>(getLocationId());
  const [productId, setProductId] = useState("");
  const [variantId, setVariantId] = useState("");
  const [threshold, setThreshold] = useState("5");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const biz = await api().listBusinesses({ status: "ACTIVE" });
        const capable = biz.filter((b) => businessHasInventory(b.capabilities));
        const current =
          businessId && capable.some((b) => b.id === businessId)
            ? businessId
            : capable[0]?.id ?? null;
        if (!current) {
          setError("No inventory-enabled business found.");
          setLoading(false);
          return;
        }
        if (current !== businessId) {
          setSelectedBusiness(current);
          setBusinessId(current);
        }
        const [locs, prods] = await Promise.all([
          api().listLocations(current),
          api().listProducts(current),
        ]);
        if (cancelled) return;
        setLocations(locs);
        setProducts(prods);
        const loc =
          locationId && locs.some((l) => l.id === locationId) ? locationId : locs[0]?.id ?? null;
        setSelectedLocation(loc);
        const firstProduct = prods[0]?.id ?? "";
        setProductId(firstProduct);
        if (firstProduct) {
          const vars = await api().listVariants(current, firstProduct);
          if (!cancelled) {
            setVariants(vars);
            setVariantId(vars[0]?.id ?? "");
          }
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load catalog");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [businessId, locationId, router]);

  async function onProductChange(id: string) {
    if (!businessId) return;
    setProductId(id);
    setError(null);
    try {
      const vars = await api().listVariants(businessId, id);
      setVariants(vars);
      setVariantId(vars[0]?.id ?? "");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load variants");
    }
  }

  async function onSubmit() {
    if (!businessId || !locationId || !variantId) {
      setError("Select a location and catalog variant.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const item = await api().upsertInventoryItem(businessId, {
        location_id: locationId,
        variant_id: variantId,
        low_stock_threshold: threshold ? Number(threshold) : undefined,
      });
      router.push(`/inventory/${item.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create stock item");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto flex max-w-xl justify-center px-5 py-20">
        <Spinner size="lg" className="text-amber-300" />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-xl px-5 py-10">
      <Link href="/inventory" className="text-sm text-amber-100/50 hover:text-amber-50">
        ← Stock board
      </Link>
      <p className="mt-4 font-display text-4xl text-amber-50">Add stock item</p>
      <p className="mt-2 text-sm text-amber-100/55">
        Link a catalog variant to a store location. Receive stock on the next screen.
      </p>

      <div className="mt-8 flex flex-col gap-4">
        <label className="flex flex-col gap-1.5 text-sm text-amber-50/80">
          <span>Location</span>
          <select
            className="rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
            value={locationId ?? ""}
            onChange={(e) => setSelectedLocation(e.target.value)}
          >
            {locations.map((loc) => (
              <option key={loc.id} value={loc.id}>
                {loc.name}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1.5 text-sm text-amber-50/80">
          <span>Product</span>
          <select
            className="rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
            value={productId}
            onChange={(e) => void onProductChange(e.target.value)}
          >
            {products.map((product) => (
              <option key={product.id} value={product.id}>
                {product.name}
              </option>
            ))}
          </select>
        </label>

        <label className="flex flex-col gap-1.5 text-sm text-amber-50/80">
          <span>Variant</span>
          <select
            className="rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
            value={variantId}
            onChange={(e) => setVariantId(e.target.value)}
          >
            {variants.map((variant) => (
              <option key={variant.id} value={variant.id}>
                {variant.name}
                {variant.sku ? ` (${variant.sku})` : ""}
              </option>
            ))}
          </select>
        </label>

        <TextField
          label="Low-stock threshold"
          type="number"
          min="0"
          value={threshold}
          onChange={(e) => setThreshold(e.target.value)}
        />
      </div>

      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      <Button className="mt-6 w-full" disabled={busy} onClick={() => void onSubmit()}>
        {busy ? "Creating…" : "Create stock item"}
      </Button>
    </main>
  );
}
