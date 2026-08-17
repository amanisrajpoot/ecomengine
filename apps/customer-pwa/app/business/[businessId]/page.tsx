"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import type { Product, Variant } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { EmptyState, ProductCard, Skeleton } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

type ProductWithVariants = Product & { variants: Variant[] };

export default function BusinessCatalogPage() {
  const params = useParams<{ businessId: string }>();
  const businessId = params.businessId;

  const [businessName, setBusinessName] = useState<string>("");
  const [products, setProducts] = useState<ProductWithVariants[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [addingVariantId, setAddingVariantId] = useState<string | null>(null);

  const loadCatalog = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      if (!session.getAccessToken()) {
        setError("Sign in to view menu.");
        return;
      }
      const api = getApiClient();
      const business = await api.getBusiness(businessId);
      setBusinessName(business.name);
      const productList = await api.listProducts(businessId, { active_only: true });
      const withVariants: ProductWithVariants[] = await Promise.all(
        productList.map(async (product) => {
          const variants = await api.listVariants(businessId, product.id, true);
          return { ...product, variants };
        }),
      );
      setProducts(withVariants);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load menu");
    } finally {
      setLoading(false);
    }
  }, [businessId]);

  useEffect(() => {
    loadCatalog();
  }, [loadCatalog]);

  async function addToCart(variant: Variant, product: Product) {
    setMessage(null);
    setError(null);
    setAddingVariantId(variant.id);
    try {
      const api = getApiClient();
      let cartId = session.getCartId();
      const existingBusinessId = session.getBusinessId();

      if (cartId && existingBusinessId && existingBusinessId !== businessId) {
        session.clearCart();
        cartId = null;
      }

      if (!cartId) {
        const cart = await api.createCart({ business_id: businessId });
        cartId = cart.id;
        session.setCartId(cartId);
        session.setBusinessId(businessId);
      }

      await api.addCartItem(cartId, { variant_id: variant.id, quantity: 1 });
      setMessage(`Added ${product.name} to cart`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add to cart");
    } finally {
      setAddingVariantId(null);
    }
  }

  return (
    <div className="space-y-4">
      <Link href="/businesses" className="text-sm font-medium text-[var(--brand)]">
        ← Back
      </Link>
      <div className="rounded-2xl bg-white p-4 shadow-sm">
        <h1 className="text-xl font-bold text-gray-900">{businessName || "Menu"}</h1>
        <p className="text-sm text-gray-500">Tap ADD to build your cart</p>
      </div>

      {message ? (
        <p className="rounded-lg bg-emerald-50 px-3 py-2 text-sm text-emerald-700">{message}</p>
      ) : null}
      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-24" />
          <Skeleton className="h-24" />
        </div>
      ) : null}

      {!loading && products.length === 0 && !error ? (
        <EmptyState title="Menu is empty" />
      ) : null}

      <div className="space-y-3">
        {products.flatMap((product) =>
          product.variants.map((variant) => (
            <ProductCard
              key={variant.id}
              name={`${product.name} — ${variant.name}`}
              description={product.description}
              pricePaise={variant.base_price_paise}
              adding={addingVariantId === variant.id}
              onAdd={() => addToCart(variant, product)}
            />
          )),
        )}
      </div>
    </div>
  );
}
