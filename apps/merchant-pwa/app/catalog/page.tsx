"use client";

import { ApiError } from "@commerce/api-client";
import type { Business, Category, Product, Variant } from "@commerce/types";
import { Button, EmptyState, ProductCard, Spinner } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { businessHasCatalog } from "../../lib/catalog-helpers";
import { api, getBusinessId, getToken, setBusinessId } from "../../lib/session";

type ProductSummary = Product & {
  variantCount: number;
  minPricePaise: number | null;
};

export default function CatalogPage() {
  const router = useRouter();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [selectedBusiness, setSelectedBusiness] = useState<string | null>(getBusinessId());
  const [categoryFilter, setCategoryFilter] = useState<string>("");
  const [showInactive, setShowInactive] = useState(true);
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const catalogBusinesses = useMemo(
    () => businesses.filter((b) => businessHasCatalog(b.capabilities)),
    [businesses],
  );

  const categoryMap = useMemo(
    () => new Map(categories.map((row) => [row.id, row.name])),
    [categories],
  );

  const loadCatalog = useCallback(
    async (businessId: string, categoryId: string, includeInactive: boolean) => {
      const [cats, prods] = await Promise.all([
        api().listCategories(businessId),
        api().listProducts(businessId, {
          active_only: !includeInactive,
          category_id: categoryId || undefined,
        }),
      ]);
      setCategories(cats);
      const summaries = await Promise.all(
        prods.map(async (product) => {
          const variants = await api().listVariants(businessId, product.id);
          const prices = variants.map((v) => v.base_price_paise);
          return {
            ...product,
            variantCount: variants.length,
            minPricePaise: prices.length > 0 ? Math.min(...prices) : null,
          };
        }),
      );
      setProducts(summaries);
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
        const capable = biz.filter((b) => businessHasCatalog(b.capabilities));
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
        await loadCatalog(current, categoryFilter, showInactive);
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
  }, [categoryFilter, loadCatalog, router, selectedBusiness, showInactive]);

  async function onBusinessChange(id: string) {
    setSelectedBusiness(id);
    setBusinessId(id);
    setCategoryFilter("");
    setLoading(true);
    setError(null);
    try {
      await loadCatalog(id, "", showInactive);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load catalog");
    } finally {
      setLoading(false);
    }
  }

  async function onCategoryChange(id: string) {
    if (!selectedBusiness) return;
    setCategoryFilter(id);
    setLoading(true);
    setError(null);
    try {
      await loadCatalog(selectedBusiness, id, showInactive);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load catalog");
    } finally {
      setLoading(false);
    }
  }

  async function onInactiveToggle(next: boolean) {
    if (!selectedBusiness) return;
    setShowInactive(next);
    setLoading(true);
    setError(null);
    try {
      await loadCatalog(selectedBusiness, categoryFilter, next);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load catalog");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <div className="flex flex-wrap items-end justify-between gap-3">
        <p className="font-display text-4xl text-amber-50">Catalog</p>
        {selectedBusiness && !loading ? (
          <Link href="/catalog/new">
            <Button variant="soft">Add product</Button>
          </Link>
        ) : null}
      </div>

      {catalogBusinesses.length === 0 && !loading ? (
        <EmptyState
          className="mt-8 border-amber-200/15"
          title="Catalog not enabled"
          description="Courier businesses do not use catalog. Switch to a food or grocery business."
        />
      ) : (
        <>
          <div className="mt-6 grid gap-4 sm:grid-cols-2">
            <label className="flex flex-col gap-1.5 text-sm text-amber-50/80">
              <span>Business</span>
              <select
                className="rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
                value={selectedBusiness ?? ""}
                onChange={(e) => void onBusinessChange(e.target.value)}
              >
                {catalogBusinesses.map((b) => (
                  <option key={b.id} value={b.id}>
                    {b.name} ({b.type})
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1.5 text-sm text-amber-50/80">
              <span>Category</span>
              <select
                className="rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
                value={categoryFilter}
                onChange={(e) => void onCategoryChange(e.target.value)}
              >
                <option value="">All categories</option>
                {categories.map((cat) => (
                  <option key={cat.id} value={cat.id}>
                    {cat.name}
                  </option>
                ))}
              </select>
            </label>
          </div>
          <label className="mt-4 flex items-center gap-2 text-sm text-amber-100/70">
            <input
              type="checkbox"
              checked={showInactive}
              onChange={(e) => void onInactiveToggle(e.target.checked)}
              className="rounded border-amber-200/20"
            />
            Show inactive products
          </label>
        </>
      )}

      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-amber-300" />
        </div>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      {!loading && catalogBusinesses.length > 0 ? (
        <ul className="mt-8 flex flex-col gap-3">
          {products.map((product) => (
            <li key={product.id}>
              <ProductCard
                product={product}
                variantCount={product.variantCount}
                minPricePaise={product.minPricePaise}
                categoryName={
                  product.category_id ? categoryMap.get(product.category_id) ?? null : null
                }
                href={`/catalog/${product.id}`}
                className="!border-amber-200/10 !bg-amber-950/25 hover:!border-amber-300/25"
              />
            </li>
          ))}
        </ul>
      ) : null}

      {!loading && !error && catalogBusinesses.length > 0 && products.length === 0 ? (
        <EmptyState
          className="mt-8 border-amber-200/15"
          title="No products yet"
          description="Add your first menu item or SKU to start selling."
          action={
            <Link href="/catalog/new">
              <Button variant="soft">Add product</Button>
            </Link>
          }
        />
      ) : null}
    </main>
  );
}
