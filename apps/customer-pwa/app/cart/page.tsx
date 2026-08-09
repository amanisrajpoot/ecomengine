"use client";

import { ApiError } from "@commerce/api-client";
import type { Cart } from "@commerce/types";
import { Button, formatPaise } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, getSessionCart, getToken, setSessionCart } from "../../lib/session";

export default function CartPage() {
  const router = useRouter();
  const [cart, setCart] = useState<Cart | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    const session = getSessionCart();
    if (!session) return;
    let cancelled = false;
    (async () => {
      try {
        const data = await api().getCart(session.cartId);
        if (!cancelled) setCart(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Cart unavailable");
          setSessionCart(null);
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router]);

  async function checkout() {
    if (!cart) return;
    setBusy(true);
    setError(null);
    try {
      const order = await api().checkout({
        cart_id: cart.id,
        payment_provider: "cod",
        fulfillment_type: "DELIVERY",
        customer_phone: "9876543210",
      });
      setSessionCart(null);
      router.push(`/orders/${order.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Checkout failed");
    } finally {
      setBusy(false);
    }
  }

  const total =
    typeof cart?.pricing_snapshot?.total_paise === "number"
      ? cart.pricing_snapshot.total_paise
      : null;

  return (
    <main className="mx-auto max-w-xl px-5 py-10">
      <p className="font-display text-4xl text-emerald-50">Cart</p>
      {!cart ? (
        <p className="mt-6 text-emerald-100/55">
          Your cart is empty. <Link href="/browse" className="text-emerald-300">Browse nearby</Link>
        </p>
      ) : (
        <>
          <ul className="mt-8 flex flex-col gap-3">
            {cart.items.map((item) => (
              <li
                key={item.id}
                className="flex items-center justify-between rounded-xl border border-emerald-200/10 px-4 py-3"
              >
                <div>
                  <p className="text-emerald-50">{item.name_snapshot}</p>
                  <p className="text-xs text-emerald-100/50">Qty {item.quantity}</p>
                </div>
                <p className="text-sm text-emerald-100/80">
                  {formatPaise(item.unit_price_paise * item.quantity)}
                </p>
              </li>
            ))}
          </ul>
          <div className="mt-6 flex items-center justify-between text-emerald-50">
            <span>Total</span>
            <span className="font-display text-2xl">
              {total != null ? formatPaise(total) : "—"}
            </span>
          </div>
          {error ? <p className="mt-3 text-sm text-rose-300">{error}</p> : null}
          <Button className="mt-6 w-full" disabled={busy || !cart.items.length} onClick={checkout}>
            {busy ? "Placing order…" : "Pay with COD"}
          </Button>
        </>
      )}
    </main>
  );
}
