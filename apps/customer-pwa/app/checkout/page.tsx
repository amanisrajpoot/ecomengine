"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import type { CartWithPricing } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Button, Card, PriceDisplay } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export default function CheckoutPage() {
  const router = useRouter();
  const [cart, setCart] = useState<CartWithPricing | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    async function load() {
      const cartId = session.getCartId();
      if (!cartId) {
        setLoading(false);
        return;
      }
      try {
        const priced = await getApiClient().priceCart(cartId);
        setCart(priced);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load cart");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function placeOrder() {
    const cartId = session.getCartId();
    if (!cartId) return;
    setSubmitting(true);
    setError(null);
    try {
      const api = getApiClient();
      const order = await api.checkoutOrder({ cart_id: cartId });
      await api.createPayment(order.id, { provider: "COD" });
      session.clearCart();
      router.push(`/orders/${order.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Checkout failed");
    } finally {
      setSubmitting(false);
    }
  }

  const pricing = cart?.pricing;

  return (
    <div className="space-y-4">
      <div>
        <Link href="/cart" className="text-xs text-emerald-300/70 hover:text-emerald-100">
          ← Cart
        </Link>
        <h1 className="mt-1 text-2xl font-semibold">Checkout</h1>
        <p className="text-sm text-emerald-200/70">Pay on delivery (COD) — captured immediately in sandbox.</p>
      </div>

      {loading ? <p className="text-sm text-emerald-200/60">Loading…</p> : null}
      {error ? <p className="text-sm text-red-300">{error}</p> : null}

      {!loading && !cart ? (
        <Card>
          <p className="text-sm text-emerald-200/70">Nothing to checkout.</p>
          <Link href="/businesses" className="mt-2 text-sm text-emerald-300 underline">
            Browse businesses
          </Link>
        </Card>
      ) : null}

      {pricing ? (
        <Card title="Order total">
          <p className="text-lg font-semibold">
            <PriceDisplay paise={pricing.total_paise} />
          </p>
          <p className="mt-2 text-sm text-emerald-200/70">
            {cart?.items?.length ?? 0} line(s) · {pricing.currency}
          </p>
        </Card>
      ) : null}

      {cart ? (
        <Button
          className="w-full sm:w-auto"
          disabled={submitting || !cart.items?.length}
          onClick={placeOrder}
        >
          {submitting ? "Placing order…" : "Place order (COD)"}
        </Button>
      ) : null}
    </div>
  );
}
