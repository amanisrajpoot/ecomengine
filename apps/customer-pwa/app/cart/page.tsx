"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { CartWithPricing } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Button, Card, PriceDisplay } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export default function CartPage() {
  const [cart, setCart] = useState<CartWithPricing | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [updatingItemId, setUpdatingItemId] = useState<string | null>(null);

  async function loadCart() {
    setLoading(true);
    setError(null);
    const cartId = session.getCartId();
    if (!cartId) {
      setCart(null);
      setLoading(false);
      return;
    }
    try {
      const priced = await getApiClient().priceCart(cartId);
      setCart(priced);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load cart");
      setCart(null);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    loadCart();
  }, []);

  async function updateQuantity(itemId: string, quantity: number) {
    const cartId = session.getCartId();
    if (!cartId || quantity < 1) return;
    setUpdatingItemId(itemId);
    try {
      await getApiClient().updateCartItem(cartId, itemId, { quantity });
      await loadCart();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Update failed");
    } finally {
      setUpdatingItemId(null);
    }
  }

  async function removeItem(itemId: string) {
    const cartId = session.getCartId();
    if (!cartId) return;
    setUpdatingItemId(itemId);
    try {
      await getApiClient().removeCartItem(cartId, itemId);
      await loadCart();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Remove failed");
    } finally {
      setUpdatingItemId(null);
    }
  }

  const pricing = cart?.pricing;

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Cart</h1>
        <p className="text-sm text-emerald-200/70">Review items and pricing before checkout.</p>
      </div>

      {loading ? <p className="text-sm text-emerald-200/60">Loading cart…</p> : null}
      {error ? <p className="text-sm text-red-300">{error}</p> : null}

      {!loading && !cart ? (
        <Card>
          <p className="text-sm text-emerald-200/70">Your cart is empty.</p>
          <Link href="/businesses" className="mt-3 inline-block text-sm text-emerald-300 underline">
            Browse businesses
          </Link>
        </Card>
      ) : null}

      {cart?.items && cart.items.length > 0 ? (
        <>
          <ul className="space-y-2">
            {cart.items.map((item) => {
              const line = pricing?.lines?.find((l) => l.cart_item_id === item.id);
              const name = line?.name ?? item.variant_id ?? item.bundle_id ?? "Item";
              return (
                <li key={item.id}>
                  <Card>
                    <div className="flex items-center justify-between gap-3">
                      <div>
                        <p className="font-medium">{name}</p>
                        <p className="text-sm text-emerald-200/70">Qty {item.quantity}</p>
                        {line ? (
                          <PriceDisplay paise={line.line_total_paise} className="text-sm" />
                        ) : null}
                      </div>
                      <div className="flex items-center gap-2">
                        <Button
                          variant="ghost"
                          disabled={updatingItemId === item.id}
                          onClick={() => updateQuantity(item.id, item.quantity - 1)}
                        >
                          −
                        </Button>
                        <Button
                          variant="ghost"
                          disabled={updatingItemId === item.id}
                          onClick={() => updateQuantity(item.id, item.quantity + 1)}
                        >
                          +
                        </Button>
                        <Button
                          variant="secondary"
                          disabled={updatingItemId === item.id}
                          onClick={() => removeItem(item.id)}
                        >
                          Remove
                        </Button>
                      </div>
                    </div>
                  </Card>
                </li>
              );
            })}
          </ul>

          {pricing ? (
            <Card title="Totals">
              <dl className="space-y-1 text-sm">
                <div className="flex justify-between">
                  <dt className="text-emerald-200/70">Subtotal</dt>
                  <dd><PriceDisplay paise={pricing.subtotal_paise} /></dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-emerald-200/70">Delivery</dt>
                  <dd><PriceDisplay paise={pricing.delivery_fee_paise} /></dd>
                </div>
                <div className="flex justify-between">
                  <dt className="text-emerald-200/70">Tax</dt>
                  <dd><PriceDisplay paise={pricing.tax_paise} /></dd>
                </div>
                <div className="flex justify-between border-t border-emerald-800/40 pt-2 font-semibold">
                  <dt>Total</dt>
                  <dd><PriceDisplay paise={pricing.total_paise} /></dd>
                </div>
              </dl>
            </Card>
          ) : null}

          <Link href="/checkout">
            <Button className="w-full sm:w-auto">Checkout</Button>
          </Link>
        </>
      ) : null}
    </div>
  );
}
