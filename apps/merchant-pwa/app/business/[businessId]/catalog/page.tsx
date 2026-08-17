"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import type { Product } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Button, Card } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export default function CatalogPage() {
  const params = useParams<{ businessId: string }>();
  const businessId = params.businessId;

  const [products, setProducts] = useState<Product[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    session.setActiveBusinessId(businessId);
    async function load() {
      setLoading(true);
      try {
        const list = await getApiClient().listProducts(businessId, { active_only: false });
        setProducts(list);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load catalog");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [businessId]);

  return (
    <div className="space-y-4">
      <Link href={`/business/${businessId}`} className="text-xs text-amber-300/70 hover:text-amber-100">
        ← Dashboard
      </Link>
      <div className="flex items-center justify-between gap-3">
        <h1 className="text-2xl font-semibold">Catalog</h1>
        <Link href={`/business/${businessId}/catalog/new`}>
          <Button variant="secondary">Add product</Button>
        </Link>
      </div>
      {loading ? <p className="text-sm text-amber-200/60">Loading…</p> : null}
      {error ? <p className="text-sm text-red-300">{error}</p> : null}

      <ul className="space-y-2">
        {products.map((product) => (
          <li key={product.id}>
            <Link href={`/business/${businessId}/catalog/${product.id}`}>
              <Card className="transition-colors hover:border-emerald-500/50">
                <p className="font-medium">{product.name}</p>
                <p className="text-xs text-amber-200/60">
                  {product.is_active ? "Active" : "Inactive"}
                </p>
              </Card>
            </Link>
          </li>
        ))}
      </ul>

      {!loading && products.length === 0 ? (
        <p className="text-sm text-amber-200/60">No products yet.</p>
      ) : null}
    </div>
  );
}
