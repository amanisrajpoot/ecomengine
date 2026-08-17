"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { PriceDisplay } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export function CartPeek() {
  const [totalPaise, setTotalPaise] = useState<number | null>(null);
  const cartId = session.getCartId();

  useEffect(() => {
    if (!cartId || !session.getAccessToken()) {
      setTotalPaise(null);
      return;
    }
    getApiClient()
      .priceCart(cartId)
      .then((cart) => setTotalPaise(cart.pricing?.total_paise ?? null))
      .catch(() => setTotalPaise(null));
  }, [cartId]);

  if (!cartId || totalPaise === null) return null;

  return (
    <div className="fixed bottom-[4.25rem] left-0 right-0 z-10 mx-auto max-w-lg px-4 safe-pb">
      <Link
        href="/cart"
        className="flex items-center justify-between rounded-xl bg-[var(--brand)] px-4 py-3 text-white shadow-lg"
      >
        <span className="text-sm font-medium">View cart</span>
        <PriceDisplay paise={totalPaise} className="!text-white font-bold" />
      </Link>
    </div>
  );
}
