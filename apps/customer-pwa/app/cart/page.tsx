"use client";

import { ApiError } from "@commerce/api-client";
import type { Cart } from "@commerce/types";
import {
  Button,
  EmptyState,
  PriceBreakdown,
  Spinner,
  TextField,
  formatPaise,
} from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import {
  api,
  getCustomerPhone,
  getDeliveryAddress,
  getSessionCart,
  getToken,
  setCustomerPhone,
  setDeliveryAddress,
  setSessionCart,
  type DeliveryAddress,
} from "../../lib/session";

export default function CartPage() {
  const router = useRouter();
  const [cart, setCart] = useState<Cart | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [phone, setPhone] = useState(getCustomerPhone());
  const [address, setAddress] = useState<DeliveryAddress>(getDeliveryAddress());
  const [itemBusy, setItemBusy] = useState<string | null>(null);

  const loadCart = useCallback(async () => {
    const session = getSessionCart();
    if (!session) {
      setCart(null);
      setLoading(false);
      return;
    }
    const data = await api().getCart(session.cartId);
    setCart(data);
    setSessionCart({
      ...session,
      itemCount: data.items.reduce((sum, item) => sum + item.quantity, 0),
    });
  }, []);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        await loadCart();
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Cart unavailable");
          setSessionCart(null);
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [loadCart, router]);

  async function updateQty(itemId: string, quantity: number) {
    const session = getSessionCart();
    if (!session || !cart) return;
    setItemBusy(itemId);
    setError(null);
    try {
      const updated =
        quantity < 1
          ? await api().removeCartItem(session.cartId, itemId)
          : await api().updateCartItem(session.cartId, itemId, { quantity });
      setCart(updated);
      setSessionCart({
        ...session,
        itemCount: updated.items.reduce((sum, item) => sum + item.quantity, 0),
      });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not update cart");
    } finally {
      setItemBusy(null);
    }
  }

  async function checkout() {
    if (!cart) return;
    setBusy(true);
    setError(null);
    setCustomerPhone(phone);
    setDeliveryAddress(address);
    try {
      const order = await api().checkout({
        cart_id: cart.id,
        payment_provider: "cod",
        fulfillment_type: "DELIVERY",
        customer_phone: phone,
        delivery_address: address,
      });
      setSessionCart(null);
      router.push(`/orders/${order.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Checkout failed");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto flex max-w-xl justify-center px-5 py-20">
        <Spinner size="lg" className="text-emerald-300" />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-xl px-5 py-10">
      <p className="font-display text-4xl text-emerald-50">Cart</p>
      {!cart || cart.items.length === 0 ? (
        <EmptyState
          className="mt-8 border-emerald-200/15"
          title="Your cart is empty"
          description="Browse nearby restaurants and stores to add items."
          action={
            <Link href="/browse">
              <Button variant="soft">Browse nearby</Button>
            </Link>
          }
        />
      ) : (
        <>
          <ul className="mt-8 flex flex-col gap-3">
            {cart.items.map((item) => (
              <li
                key={item.id}
                className="rounded-xl border border-emerald-200/10 px-4 py-3"
              >
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="text-emerald-50">{item.name_snapshot}</p>
                    <p className="text-xs text-emerald-100/50">
                      {formatPaise(item.unit_price_paise)} each
                    </p>
                  </div>
                  <p className="text-sm text-emerald-100/80">
                    {formatPaise(item.unit_price_paise * item.quantity)}
                  </p>
                </div>
                <div className="mt-3 flex items-center gap-2">
                  <button
                    type="button"
                    disabled={itemBusy === item.id}
                    className="flex h-8 w-8 items-center justify-center rounded-lg border border-emerald-200/15 text-emerald-50 hover:bg-emerald-400/10 disabled:opacity-50"
                    onClick={() => updateQty(item.id, item.quantity - 1)}
                    aria-label="Decrease quantity"
                  >
                    −
                  </button>
                  <span className="min-w-[2rem] text-center text-sm text-emerald-50">
                    {item.quantity}
                  </span>
                  <button
                    type="button"
                    disabled={itemBusy === item.id}
                    className="flex h-8 w-8 items-center justify-center rounded-lg border border-emerald-200/15 text-emerald-50 hover:bg-emerald-400/10 disabled:opacity-50"
                    onClick={() => updateQty(item.id, item.quantity + 1)}
                    aria-label="Increase quantity"
                  >
                    +
                  </button>
                  <button
                    type="button"
                    disabled={itemBusy === item.id}
                    className="ml-auto text-xs text-rose-300 hover:text-rose-200"
                    onClick={() => updateQty(item.id, 0)}
                  >
                    Remove
                  </button>
                </div>
              </li>
            ))}
          </ul>

          <div className="mt-6">
            <PriceBreakdown snapshot={cart.pricing_snapshot} />
          </div>

          <div className="mt-6 space-y-4">
            <p className="text-sm font-medium text-emerald-50/90">Delivery address</p>
            <TextField
              label="Street / building"
              value={address.line1}
              onChange={(e) => setAddress((prev) => ({ ...prev, line1: e.target.value }))}
              required
            />
            <div className="grid grid-cols-2 gap-3">
              <TextField
                label="City"
                value={address.city}
                onChange={(e) => setAddress((prev) => ({ ...prev, city: e.target.value }))}
                required
              />
              <TextField
                label="Pincode"
                value={address.pincode}
                onChange={(e) => setAddress((prev) => ({ ...prev, pincode: e.target.value }))}
                pattern="[0-9]{6}"
                required
              />
            </div>
            <TextField
              label="Phone for delivery updates"
              type="tel"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              placeholder="10-digit mobile number"
              pattern="[0-9]{10}"
              required
            />
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
