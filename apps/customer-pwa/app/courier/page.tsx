"use client";

import { ApiError } from "@commerce/api-client";
import type { CourierQuote, Order } from "@commerce/types";
import { Button, TextField, formatPaise } from "@commerce/ui";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import { api, getToken } from "../../lib/session";

export default function CourierPage() {
  const router = useRouter();
  const [businessId, setBusinessId] = useState(
    process.env.NEXT_PUBLIC_COURIER_BUSINESS_ID ?? "",
  );
  const [weightKg, setWeightKg] = useState("2");
  const [vehicle, setVehicle] = useState("BIKE");
  const [express, setExpress] = useState(false);
  const [quote, setQuote] = useState<CourierQuote | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const pickup = { lat: 12.9716, lng: 77.5946, address: { line1: "MG Road Hub", city: "Bengaluru", state: "Karnataka", pincode: "560001" } };
  const drop = { lat: 12.9352, lng: 77.6245, address: { line1: "Koramangala 5th Block", city: "Bengaluru", state: "Karnataka", pincode: "560095" } };

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  async function onQuote(event: FormEvent) {
    event.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const result = await api().courierQuote({
        pickup,
        drop,
        weight_kg: Number(weightKg),
        vehicle_type: vehicle,
        express,
        business_id: businessId || undefined,
      });
      setQuote(result);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Quote failed");
    } finally {
      setBusy(false);
    }
  }

  async function book() {
    if (!businessId.trim()) {
      setError("Courier business ID is required to book.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const order: Order = await api().createShipment({
        business_id: businessId.trim(),
        pickup,
        drop,
        weight_kg: Number(weightKg),
        vehicle_type: vehicle,
        express,
        payment_provider: "cod",
        customer_phone: "9876543210",
        package_notes: "Customer PWA shipment",
      });
      router.push(`/orders/${order.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Booking failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-xl px-5 py-10">
      <p className="font-display text-4xl text-emerald-50">Courier</p>
      <p className="mt-2 text-sm text-emerald-100/55">
        Demo route: MG Road → Koramangala. Quote by distance, weight, and vehicle.
        {process.env.NEXT_PUBLIC_COURIER_BUSINESS_ID
          ? " Courier business loaded from environment."
          : ""}
      </p>
      <form onSubmit={onQuote} className="mt-8 flex flex-col gap-4">
        {!process.env.NEXT_PUBLIC_COURIER_BUSINESS_ID ? (
          <TextField
            label="Courier business ID"
            value={businessId}
            onChange={(e) => setBusinessId(e.target.value)}
            placeholder="COURIER business UUID"
          />
        ) : null}
        <TextField
          label="Weight (kg)"
          type="number"
          step="0.1"
          min="0.1"
          value={weightKg}
          onChange={(e) => setWeightKg(e.target.value)}
          required
        />
        <label className="flex flex-col gap-1.5 text-sm text-emerald-50/80">
          <span>Vehicle</span>
          <select
            className="rounded-xl border border-emerald-200/15 bg-emerald-950/40 px-3 py-2.5 text-emerald-50"
            value={vehicle}
            onChange={(e) => setVehicle(e.target.value)}
          >
            {["BIKE", "SCOOTER", "CAR", "VAN"].map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
        </label>
        <label className="flex items-center gap-2 text-sm text-emerald-50/80">
          <input
            type="checkbox"
            checked={express}
            onChange={(e) => setExpress(e.target.checked)}
          />
          Express surcharge
        </label>
        <Button type="submit" disabled={busy}>
          {busy ? "Quoting…" : "Get quote"}
        </Button>
      </form>

      {quote ? (
        <div className="mt-8 rounded-2xl border border-emerald-200/15 bg-emerald-950/30 p-5">
          <p className="text-sm text-emerald-100/60">
            {quote.distance_km.toFixed(1)} km · {quote.vehicle_type}
            {quote.express ? " · express" : ""}
          </p>
          <p className="mt-2 font-display text-3xl text-emerald-50">
            {formatPaise(quote.pricing.total_paise)}
          </p>
          <Button className="mt-4 w-full" variant="soft" disabled={busy} onClick={book}>
            Book COD shipment
          </Button>
        </div>
      ) : null}
      {error ? <p className="mt-4 text-sm text-rose-300">{error}</p> : null}
    </main>
  );
}
