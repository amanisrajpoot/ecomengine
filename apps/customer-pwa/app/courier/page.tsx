"use client";

import { ApiError } from "@commerce/api-client";
import type { CourierQuote, Order } from "@commerce/types";
import { Button, TextField, formatPaise } from "@commerce/ui";
import { useRouter } from "next/navigation";
import { FormEvent, useEffect, useState } from "react";

import {
  api,
  DEFAULT_DELIVERY_ADDRESS,
  getCustomerPhone,
  getDeliveryAddress,
  getToken,
} from "../../lib/session";

type StopAddress = {
  lat: number;
  lng: number;
  address: { line1: string; city: string; state: string; pincode: string };
};

const DEFAULT_PICKUP: StopAddress = {
  lat: 12.9716,
  lng: 77.5946,
  address: {
    line1: "MG Road Hub",
    city: "Bengaluru",
    state: "Karnataka",
    pincode: "560001",
  },
};

function toStopAddress(
  line1: string,
  city: string,
  pincode: string,
  lat?: number,
  lng?: number,
): StopAddress {
  return {
    lat: lat ?? DEFAULT_DELIVERY_ADDRESS.lat ?? 12.9352,
    lng: lng ?? DEFAULT_DELIVERY_ADDRESS.lng ?? 77.6245,
    address: {
      line1,
      city,
      state: "Karnataka",
      pincode,
    },
  };
}

export default function CourierPage() {
  const router = useRouter();
  const savedDrop = getDeliveryAddress();
  const [businessId, setBusinessId] = useState(
    process.env.NEXT_PUBLIC_COURIER_BUSINESS_ID ?? "",
  );
  const [pickupLine1, setPickupLine1] = useState(DEFAULT_PICKUP.address.line1);
  const [pickupCity, setPickupCity] = useState(DEFAULT_PICKUP.address.city);
  const [pickupPincode, setPickupPincode] = useState(DEFAULT_PICKUP.address.pincode);
  const [dropLine1, setDropLine1] = useState(savedDrop.line1);
  const [dropCity, setDropCity] = useState(savedDrop.city);
  const [dropPincode, setDropPincode] = useState(savedDrop.pincode);
  const [weightKg, setWeightKg] = useState("2");
  const [vehicle, setVehicle] = useState("BIKE");
  const [express, setExpress] = useState(false);
  const [quote, setQuote] = useState<CourierQuote | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const pickup = toStopAddress(pickupLine1, pickupCity, pickupPincode, DEFAULT_PICKUP.lat, DEFAULT_PICKUP.lng);
  const drop = toStopAddress(dropLine1, dropCity, dropPincode, savedDrop.lat, savedDrop.lng);

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
        customer_phone: getCustomerPhone(),
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
        Quote by distance, weight, and vehicle. Edit pickup and drop addresses below.
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
        <fieldset className="space-y-3 rounded-xl border border-emerald-200/10 p-4">
          <legend className="px-1 text-sm font-medium text-emerald-50/90">Pickup</legend>
          <TextField
            label="Street / building"
            value={pickupLine1}
            onChange={(e) => setPickupLine1(e.target.value)}
            required
          />
          <div className="grid grid-cols-2 gap-3">
            <TextField
              label="City"
              value={pickupCity}
              onChange={(e) => setPickupCity(e.target.value)}
              required
            />
            <TextField
              label="Pincode"
              value={pickupPincode}
              onChange={(e) => setPickupPincode(e.target.value)}
              required
            />
          </div>
        </fieldset>
        <fieldset className="space-y-3 rounded-xl border border-emerald-200/10 p-4">
          <legend className="px-1 text-sm font-medium text-emerald-50/90">Drop</legend>
          <TextField
            label="Street / building"
            value={dropLine1}
            onChange={(e) => setDropLine1(e.target.value)}
            required
          />
          <div className="grid grid-cols-2 gap-3">
            <TextField
              label="City"
              value={dropCity}
              onChange={(e) => setDropCity(e.target.value)}
              required
            />
            <TextField
              label="Pincode"
              value={dropPincode}
              onChange={(e) => setDropPincode(e.target.value)}
              required
            />
          </div>
        </fieldset>
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
