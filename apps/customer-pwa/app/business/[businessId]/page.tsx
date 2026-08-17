"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import type { Product, Variant } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Button, Card, PriceDisplay } from "@commerce/ui";

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
        setError("Sign in to view catalog.");
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
      setError(err instanceof ApiError ? err.message : "Failed to load catalog");
    } finally {
      setLoading(false);
    }
  }, [businessId]);

  useEffect(() => {
    loadCatalog();
  }, [loadCatalog]);

  async function addToCart(variant: Variant) {
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
      setMessage(`Added ${variant.name} to cart.`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add to cart");
    } finally {
      setAddingVariantId(null);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <Link href="/businesses" className="text-xs text-emerald-300/70 hover:text-emerald-100">
          ← Businesses
        </Link>
        <h1 className="mt-1 text-2xl font-semibold">{businessName || "Catalog"}</h1>
      </div>

      {loading ? <p className="text-sm text-emerald-200/60">Loading catalog…</p> : null}
      {error ? <p className="text-sm text-red-300">{error}</p> : null}
      {message ? <p className="text-sm text-emerald-300">{message}</p> : null}

      <div className="space-y-4">
        {products.map((product) => (
          <Card key={product.id} title={product.name}>
            {product.description ? (
              <p className="mb-3 text-sm text-emerald-200/70">{product.description}</p>
            ) : null}
            {product.variants.length === 0 ? (
              <p className="text-sm text-emerald-200/50">No variants available.</p>
            ) : (
              <ul className="space-y-2">
                {product.variants.map((variant) => (
                  <li
                    key={variant.id}
                    className="flex items-center justify-between gap-3 rounded-lg bg-emerald-950/50 px-3 py-2"
                  >
                    <div>
                      <p className="font-medium">{variant.name}</p>
                      <PriceDisplay paise={variant.base_price_paise} />
                    </div>
                    <Button
                      variant="secondary"
                      disabled={addingVariantId === variant.id}
                      onClick={() => addToCart(variant)}
                    >
                      {addingVariantId === variant.id ? "Adding…" : "Add"}
                    </Button>
                  </li>
                ))}
              </ul>
            )}
          </Card>
        ))}
      </div>

      {!loading && products.length === 0 && !error ? (
        <p className="text-sm text-emerald-200/60">No products in this catalog.</p>
      ) : null}

      <Link href="/cart">
        <Button>View cart</Button>
      </Link>
    </div>
  );
}
