"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import type { Product } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Badge, Button, EmptyState, Skeleton } from "@commerce/ui";

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
    <div className="space-y-5">
      <div className="flex items-start justify-between gap-3">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">Menu</h1>
          <p className="text-sm text-gray-500">Products and variants for this store.</p>
        </div>
        <Link href={`/business/${businessId}/catalog/new`}>
          <Button variant="brand">Add item</Button>
        </Link>
      </div>

      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-16" />
          <Skeleton className="h-16" />
        </div>
      ) : null}

      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      <ul className="space-y-3">
        {products.map((product) => (
          <li key={product.id}>
            <Link
              href={`/business/${businessId}/catalog/${product.id}`}
              className="flex items-center justify-between gap-3 rounded-2xl border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
            >
              <div>
                <p className="font-semibold text-gray-900">{product.name}</p>
                {product.description ? (
                  <p className="mt-1 text-sm text-gray-500 line-clamp-1">{product.description}</p>
                ) : null}
              </div>
              <Badge variant={product.is_active ? "accent" : "muted"}>
                {product.is_active ? "Active" : "Inactive"}
              </Badge>
            </Link>
          </li>
        ))}
      </ul>

      {!loading && products.length === 0 ? (
        <EmptyState
          title="No menu items"
          description="Add products so customers can order from this store."
          action={
            <Link href={`/business/${businessId}/catalog/new`}>
              <Button variant="brand">Add first item</Button>
            </Link>
          }
        />
      ) : null}
    </div>
  );
}
