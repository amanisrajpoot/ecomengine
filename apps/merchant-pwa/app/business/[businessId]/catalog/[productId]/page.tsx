"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import type { Product, Variant } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Button, Card, Input, PriceDisplay } from "@commerce/ui";

import { getApiClient } from "@/lib/api";

export default function ProductDetailPage() {
  const params = useParams<{ businessId: string; productId: string }>();
  const { businessId, productId } = params;

  const [product, setProduct] = useState<Product | null>(null);
  const [variants, setVariants] = useState<Variant[]>([]);
  const [variantName, setVariantName] = useState("");
  const [priceRupees, setPriceRupees] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [adding, setAdding] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const api = getApiClient();
      const p = await api.getProduct(businessId, productId);
      const v = await api.listVariants(businessId, productId, false);
      setProduct(p);
      setVariants(v);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load product");
    } finally {
      setLoading(false);
    }
  }, [businessId, productId]);

  useEffect(() => {
    load();
  }, [load]);

  async function addVariant(e: React.FormEvent) {
    e.preventDefault();
    const rupees = Number(priceRupees);
    if (!Number.isFinite(rupees) || rupees <= 0) {
      setError("Enter a valid price in rupees.");
      return;
    }
    setAdding(true);
    setError(null);
    try {
      await getApiClient().createVariant(businessId, productId, {
        name: variantName,
        base_price_paise: Math.round(rupees * 100),
      });
      setVariantName("");
      setPriceRupees("");
      await load();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add variant");
    } finally {
      setAdding(false);
    }
  }

  return (
    <div className="space-y-4">
      <Link
        href={`/business/${businessId}/catalog`}
        className="text-xs text-amber-300/70 hover:text-amber-100"
      >
        ← Catalog
      </Link>
      <h1 className="text-2xl font-semibold">{product?.name ?? "Product"}</h1>
      {product?.description ? (
        <p className="text-sm text-amber-200/70">{product.description}</p>
      ) : null}
      {loading ? <p className="text-sm text-amber-200/60">Loading…</p> : null}
      {error ? <p className="text-sm text-red-300">{error}</p> : null}

      <Card title="Variants">
        {variants.length === 0 ? (
          <p className="text-sm text-amber-200/60">No variants yet.</p>
        ) : (
          <ul className="space-y-2">
            {variants.map((variant) => (
              <li
                key={variant.id}
                className="flex justify-between gap-3 rounded-lg bg-emerald-950/40 px-3 py-2 text-sm"
              >
                <span>{variant.name}</span>
                <PriceDisplay paise={variant.base_price_paise} />
              </li>
            ))}
          </ul>
        )}
      </Card>

      <Card title="Add variant">
        <form className="space-y-3" onSubmit={addVariant}>
          <Input
            label="Variant name"
            value={variantName}
            onChange={(e) => setVariantName(e.target.value)}
            required
          />
          <Input
            label="Price (₹)"
            type="number"
            min="0.01"
            step="0.01"
            value={priceRupees}
            onChange={(e) => setPriceRupees(e.target.value)}
            required
          />
          <Button type="submit" disabled={adding || !variantName.trim()}>
            {adding ? "Adding…" : "Add variant"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
