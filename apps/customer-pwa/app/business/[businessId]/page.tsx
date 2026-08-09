"use client";

import { ApiError } from "@commerce/api-client";
import type { Product, Variant } from "@commerce/types";
import { Button, formatPaise } from "@commerce/ui";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import {
  api,
  getSessionCart,
  getToken,
  setSessionCart,
} from "../../../lib/session";

type Row = Product & { variants: Variant[] };

function BusinessInner() {
  const router = useRouter();
  const params = useParams<{ businessId: string }>();
  const search = useSearchParams();
  const locationId = search.get("location");
  const [name, setName] = useState("Menu");
  const [rows, setRows] = useState<Row[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const client = api();
        const business = await client.getBusiness(params.businessId);
        const products = await client.listProducts(params.businessId);
        const withVariants: Row[] = [];
        for (const product of products) {
          const variants = await client.listVariants(params.businessId, product.id);
          withVariants.push({ ...product, variants });
        }
        if (!cancelled) {
          setName(business.name);
          setRows(withVariants);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load catalog");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [params.businessId, router]);

  async function addVariant(variant: Variant) {
    setBusyId(variant.id);
    setError(null);
    try {
      const client = api();
      let cart = getSessionCart();
      if (!cart || cart.businessId !== params.businessId) {
        const created = await client.createCart({
          business_id: params.businessId,
          location_id: locationId,
        });
        cart = {
          cartId: created.id,
          businessId: params.businessId,
          locationId,
        };
        setSessionCart(cart);
      }
      await client.addCartItem(cart.cartId, { variant_id: variant.id, quantity: 1 });
      router.push("/cart");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add to cart");
    } finally {
      setBusyId(null);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <p className="font-display text-4xl text-emerald-50">{name}</p>
      <p className="mt-2 text-sm text-emerald-100/55">Tap a variant to add it to your cart.</p>
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      <ul className="mt-8 flex flex-col gap-6">
        {rows.map((product) => (
          <li key={product.id} className="border-t border-emerald-200/10 pt-5">
            <p className="text-lg font-medium text-emerald-50">{product.name}</p>
            {product.description ? (
              <p className="mt-1 text-sm text-emerald-100/50">{product.description}</p>
            ) : null}
            <ul className="mt-3 flex flex-col gap-2">
              {product.variants.map((variant) => (
                <li
                  key={variant.id}
                  className="flex items-center justify-between gap-3 rounded-xl bg-emerald-950/30 px-3 py-2"
                >
                  <div>
                    <p className="text-sm text-emerald-50">{variant.name}</p>
                    <p className="text-xs text-emerald-100/50">
                      {formatPaise(variant.base_price_paise)}
                    </p>
                  </div>
                  <Button
                    type="button"
                    variant="soft"
                    disabled={!variant.is_available || busyId === variant.id}
                    onClick={() => addVariant(variant)}
                  >
                    {busyId === variant.id ? "Adding…" : "Add"}
                  </Button>
                </li>
              ))}
            </ul>
          </li>
        ))}
      </ul>
    </main>
  );
}

export default function BusinessPage() {
  return (
    <Suspense fallback={<main className="px-5 py-10 text-emerald-100/50">Loading…</main>}>
      <BusinessInner />
    </Suspense>
  );
}
