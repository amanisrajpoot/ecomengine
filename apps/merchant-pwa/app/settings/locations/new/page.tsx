"use client";

import { ApiError } from "@commerce/api-client";
import type { DayHours } from "@commerce/types";
import { Button, Spinner, TextField, useToast } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { AddressFields, HoursEditor } from "../../../../components/LocationFormFields";
import { defaultHours } from "../../../../lib/settings-helpers";
import { api, getBusinessId, getToken } from "../../../../lib/session";

export default function NewLocationPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [businessId, setBusinessId] = useState<string | null>(getBusinessId());
  const [name, setName] = useState("");
  const [line1, setLine1] = useState("");
  const [city, setCity] = useState("Bengaluru");
  const [state, setStateVal] = useState("Karnataka");
  const [pincode, setPincode] = useState("560038");
  const [lat, setLat] = useState("12.9716");
  const [lng, setLng] = useState("77.5946");
  const [hours, setHours] = useState<DayHours[]>(defaultHours());
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    setBusinessId(getBusinessId());
    setLoading(false);
  }, [router]);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!businessId || !name.trim() || !line1.trim()) {
      setError("Name and address are required.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const location = await api().createLocation(businessId, {
        name: name.trim(),
        address: { line1: line1.trim(), city, state, pincode, country: "IN" },
        lat: Number.parseFloat(lat),
        lng: Number.parseFloat(lng),
        hours,
        is_active: true,
      });
      toast({ title: "Location created", variant: "success" });
      router.push(`/settings/locations/${location.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create location");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto max-w-lg px-5 py-16">
        <Spinner size="lg" className="text-amber-300" />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-lg px-5 py-10">
      <Link href="/settings/locations" className="text-sm text-amber-100/50 hover:text-amber-50">
        ← Locations
      </Link>
      <p className="mt-4 font-display text-4xl text-amber-50">New location</p>

      <form className="mt-8 flex flex-col gap-5" onSubmit={onSubmit}>
        <TextField
          label="Location name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
        />
        <AddressFields
          line1={line1}
          city={city}
          state={state}
          pincode={pincode}
          onChange={(field, value) => {
            if (field === "line1") setLine1(value);
            if (field === "city") setCity(value);
            if (field === "state") setStateVal(value);
            if (field === "pincode") setPincode(value);
          }}
        />
        <div className="grid gap-3 sm:grid-cols-2">
          <TextField
            label="Latitude"
            value={lat}
            onChange={(e) => setLat(e.target.value)}
            className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
          />
          <TextField
            label="Longitude"
            value={lng}
            onChange={(e) => setLng(e.target.value)}
            className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
          />
        </div>
        <div>
          <p className="mb-2 text-sm font-medium text-amber-50/80">Hours</p>
          <HoursEditor hours={hours} onChange={setHours} />
        </div>
        {error ? <p className="text-rose-300">{error}</p> : null}
        <Button type="submit" disabled={busy}>
          {busy ? "Creating…" : "Create location"}
        </Button>
      </form>
    </main>
  );
}
