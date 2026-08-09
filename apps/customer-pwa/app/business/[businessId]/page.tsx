"use client";

import { ApiError } from "@commerce/api-client";
import type { Addon, Product, ProductAddonLink, Variant } from "@commerce/types";
import { Button, EmptyState, formatPaise, Spinner } from "@commerce/ui";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";

import {
  api,
  getSessionCart,
  getToken,
  setSessionCart,
} from "../../../lib/session";

type Row = Product & { variants: Variant[]; addons: Addon[] };

function BusinessInner() {
  const router = useRouter();
  const params = useParams<{ businessId: string }>();
  const search = useSearchParams();
  const locationId = search.get("location");
  const [name, setName] = useState("Menu");
  const [rows, setRows] = useState<Row[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [picker, setPicker] = useState<{
    product: Row;
    variant: Variant;
    selected: Record<string, number>;
  } | null>(null);

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
          let addons: Addon[] = [];
          try {
            const links = await client.listProductAddons(params.businessId, product.id);
            if (links.length) {
              const allAddons = await client.listAddons(params.businessId);
              const linkedIds = new Set(links.map((l: ProductAddonLink) => l.addon_id));
              addons = allAddons.filter((a) => linkedIds.has(a.id) && a.is_active);
            }
          } catch {
            addons = [];
          }
          withVariants.push({ ...product, variants, addons });
        }
        if (!cancelled) {
          setName(business.name);
          setRows(withVariants);
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
  }, [params.businessId, router]);

  function openPicker(product: Row, variant: Variant) {
    if (product.addons.length) {
      setPicker({ product, variant, selected: {} });
      return;
    }
    void addVariant(variant, []);
  }

  async function addVariant(
    variant: Variant,
    addons: Array<{ addon_id: string; quantity: number }>,
  ) {
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
      }
      const updated = await client.addCartItem(cart.cartId, {
        variant_id: variant.id,
        quantity: 1,
        addons,
      });
      setSessionCart({
        ...cart,
        itemCount: updated.items.reduce((sum, item) => sum + item.quantity, 0),
      });
      setPicker(null);
      router.push("/cart");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add to cart");
    } finally {
      setBusyId(null);
    }
  }

  function toggleAddon(addon: Addon) {
    if (!picker) return;
    setPicker((prev) => {
      if (!prev) return prev;
      const next = { ...prev.selected };
      if (next[addon.id]) delete next[addon.id];
      else next[addon.id] = 1;
      return { ...prev, selected: next };
    });
  }

  if (loading) {
    return (
      <main className="mx-auto flex max-w-3xl justify-center px-5 py-20">
        <Spinner size="lg" className="text-emerald-300" />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <p className="font-display text-4xl text-emerald-50">{name}</p>
      <p className="mt-2 text-sm text-emerald-100/55">Tap a variant to add it to your cart.</p>
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      {rows.length === 0 ? (
        <EmptyState
          className="mt-8 border-emerald-200/15"
          title="No items available"
          description="This business has no active menu items yet."
        />
      ) : (
        <ul className="mt-8 flex flex-col gap-6">
          {rows.map((product) => (
            <li key={product.id} className="border-t border-emerald-200/10 pt-5">
              <p className="text-lg font-medium text-emerald-50">{product.name}</p>
              {product.description ? (
                <p className="mt-1 text-sm text-emerald-100/50">{product.description}</p>
              ) : null}
              {product.addons.length > 0 ? (
                <p className="mt-1 text-xs text-emerald-300/60">
                  Customizable · {product.addons.length} add-on
                  {product.addons.length > 1 ? "s" : ""}
                </p>
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
                      onClick={() => openPicker(product, variant)}
                    >
                      {busyId === variant.id ? "Adding…" : "Add"}
                    </Button>
                  </li>
                ))}
              </ul>
            </li>
          ))}
        </ul>
      )}

      {picker ? (
        <div className="fixed inset-0 z-30 flex items-end justify-center bg-black/60 p-4 sm:items-center">
          <div className="w-full max-w-md rounded-2xl border border-emerald-200/15 bg-[#0f1c14] p-5 shadow-xl">
            <p className="font-medium text-emerald-50">{picker.variant.name}</p>
            <p className="text-sm text-emerald-100/55">Optional add-ons</p>
            <ul className="mt-4 flex flex-col gap-2">
              {picker.product.addons.map((addon) => {
                const checked = Boolean(picker.selected[addon.id]);
                return (
                  <li key={addon.id}>
                    <label className="flex cursor-pointer items-center justify-between rounded-xl border border-emerald-200/10 px-3 py-2">
                      <span className="flex items-center gap-2 text-sm text-emerald-50">
                        <input
                          type="checkbox"
                          checked={checked}
                          onChange={() => toggleAddon(addon)}
                        />
                        {addon.name}
                      </span>
                      <span className="text-xs text-emerald-100/60">
                        +{formatPaise(addon.price_paise)}
                      </span>
                    </label>
                  </li>
                );
              })}
            </ul>
            <div className="mt-5 flex gap-2">
              <Button type="button" variant="ghost" className="flex-1" onClick={() => setPicker(null)}>
                Cancel
              </Button>
              <Button
                type="button"
                className="flex-1"
                disabled={busyId === picker.variant.id}
                onClick={() => {
                  const addons = Object.entries(picker.selected).map(([addon_id, quantity]) => ({
                    addon_id,
                    quantity,
                  }));
                  void addVariant(picker.variant, addons);
                }}
              >
                Add to cart
              </Button>
            </div>
          </div>
        </div>
      ) : null}
    </main>
  );
}

export default function BusinessPage() {
  return (
    <Suspense
      fallback={
        <main className="flex justify-center px-5 py-20">
          <Spinner className="text-emerald-300" />
        </main>
      }
    >
      <BusinessInner />
    </Suspense>
  );
}
