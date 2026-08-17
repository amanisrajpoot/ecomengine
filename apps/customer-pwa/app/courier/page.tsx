"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { Business, CourierQuoteResponse } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Button, Card, Input, PriceDisplay } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export default function CourierPage() {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [businessId, setBusinessId] = useState("");
  const [weightKg, setWeightKg] = useState("1");
  const [express, setExpress] = useState(false);
  const [quote, setQuote] = useState<CourierQuoteResponse | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!session.getAccessToken()) return;
    getApiClient()
      .listBusinesses({ status: "ACTIVE", type: "COURIER" })
      .then((list) => {
        setBusinesses(list);
        if (list[0]) setBusinessId(list[0].id);
      })
      .catch(() => undefined);
  }, []);

  async function requestQuote() {
    setError(null);
    setMessage(null);
    setLoading(true);
    try {
      if (!businessId) throw new Error("Select a courier business.");
      const weight = Number(weightKg);
      if (!Number.isFinite(weight) || weight <= 0) throw new Error("Invalid weight.");

      const result = await getApiClient().quoteCourier({
        business_id: businessId,
        pickup: { lat: 12.9716, lng: 77.5946, address: { city: "Bengaluru" } },
        drop: { lat: 12.975, lng: 77.6, address: { city: "Bengaluru" } },
        weight_kg: weight,
        vehicle_type: "BIKE",
        express,
      });
      setQuote(result);
    } catch (err) {
      setQuote(null);
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Quote failed",
      );
    } finally {
      setLoading(false);
    }
  }

  async function addQuoteToCart() {
    if (!quote) return;
    setError(null);
    setMessage(null);
    setLoading(true);
    try {
      const api = getApiClient();
      let cartId = session.getCartId();
      if (!cartId || session.getBusinessId() !== businessId) {
        session.clearCart();
        const cart = await api.createCart({ business_id: businessId });
        cartId = cart.id;
        session.setCartId(cartId);
        session.setBusinessId(businessId);
      }
      await api.addCartItem(cartId, {
        quantity: 1,
        meta: quote.quote,
      });
      setMessage("Courier quote added to cart. Proceed to checkout.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not add quote to cart");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Courier quote</h1>
        <p className="text-sm text-emerald-200/70">
          Get a fare estimate and add it to your cart (demo pickup/drop in Bengaluru).
        </p>
      </div>

      {!session.getAccessToken() ? (
        <p className="text-sm text-emerald-200/70">
          <Link href="/login" className="underline">Sign in</Link> to request quotes.
        </p>
      ) : null}

      <Card>
        <div className="space-y-3">
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="text-emerald-200/80">Courier business</span>
            <select
              className="rounded-lg border border-emerald-700/40 bg-emerald-950/60 px-3 py-2"
              value={businessId}
              onChange={(e) => setBusinessId(e.target.value)}
            >
              {businesses.map((b) => (
                <option key={b.id} value={b.id}>{b.name}</option>
              ))}
            </select>
          </label>
          <Input
            label="Weight (kg)"
            type="number"
            min="0.1"
            step="0.1"
            value={weightKg}
            onChange={(e) => setWeightKg(e.target.value)}
          />
          <label className="flex items-center gap-2 text-sm text-emerald-200/80">
            <input
              type="checkbox"
              checked={express}
              onChange={(e) => setExpress(e.target.checked)}
            />
            Express delivery
          </label>
          <Button disabled={loading || !session.getAccessToken()} onClick={requestQuote}>
            {loading ? "Working…" : "Get quote"}
          </Button>
        </div>
      </Card>

      {quote ? (
        <Card title="Quote">
          <p className="text-lg font-semibold">
            <PriceDisplay
              paise={
                typeof quote.breakdown.total_paise === "number"
                  ? quote.breakdown.total_paise
                  : 0
              }
            />
          </p>
          <p className="mt-2 text-sm text-emerald-200/70">
            {typeof quote.quote.distance_km === "number"
              ? `${quote.quote.distance_km.toFixed(1)} km`
              : "—"}
            {typeof quote.quote.vehicle_type === "string" ? ` · ${quote.quote.vehicle_type}` : ""}
            {quote.quote.express === true ? " · express" : ""}
          </p>
          <Button className="mt-3" variant="secondary" disabled={loading} onClick={addQuoteToCart}>
            Add to cart
          </Button>
        </Card>
      ) : null}

      {message ? <p className="text-sm text-emerald-300">{message}</p> : null}
      {error ? <p className="text-sm text-red-300">{error}</p> : null}

      {quote && message ? (
        <Link href="/checkout" className="text-sm text-emerald-300 underline">
          Go to checkout
        </Link>
      ) : null}
    </div>
  );
}
