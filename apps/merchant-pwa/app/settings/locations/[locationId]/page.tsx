"use client";

import { ApiError } from "@commerce/api-client";
import type { BusinessLocation, DayHours } from "@commerce/types";
import { Button, Spinner, TextField, useToast } from "@commerce/ui";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { AddressFields, HoursEditor } from "../../../../components/LocationFormFields";
import { addressField, normalizeHours } from "../../../../lib/settings-helpers";
import { api, getBusinessId, getToken } from "../../../../lib/session";

export default function LocationDetailPage() {
  const router = useRouter();
  const params = useParams<{ locationId: string }>();
  const { toast } = useToast();
  const [businessId, setBusinessId] = useState<string | null>(getBusinessId());
  const [location, setLocation] = useState<BusinessLocation | null>(null);
  const [name, setName] = useState("");
  const [line1, setLine1] = useState("");
  const [city, setCity] = useState("");
  const [state, setStateVal] = useState("");
  const [pincode, setPincode] = useState("");
  const [lat, setLat] = useState("");
  const [lng, setLng] = useState("");
  const [hours, setHours] = useState<DayHours[]>([]);
  const [isActive, setIsActive] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const load = useCallback(async () => {
    const bid = getBusinessId();
    if (!bid) throw new Error("Select a business first");
    setBusinessId(bid);
    const row = await api().getLocation(bid, params.locationId);
    setLocation(row);
    setName(row.name);
    setLine1(addressField(row.address, "line1"));
    setCity(addressField(row.address, "city", "Bengaluru"));
    setStateVal(addressField(row.address, "state", "Karnataka"));
    setPincode(addressField(row.address, "pincode"));
    setLat(String(row.lat));
    setLng(String(row.lng));
    setHours(normalizeHours(row.hours));
    setIsActive(row.is_active);
  }, [params.locationId]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        await load();
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load location");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [load, router]);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!businessId) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await api().updateLocation(businessId, params.locationId, {
        name: name.trim(),
        address: { line1: line1.trim(), city, state, pincode, country: "IN" },
        lat: Number.parseFloat(lat),
        lng: Number.parseFloat(lng),
        hours,
        is_active: isActive,
      });
      setLocation(updated);
      toast({ title: "Location updated", variant: "success" });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save location");
    } finally {
      setSaving(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto max-w-lg px-5 py-16">
        <Spinner size="lg" className="text-amber-300" />
      </main>
    );
  }

  if (!location) {
    return (
      <main className="mx-auto max-w-lg px-5 py-10">
        <p className="text-rose-300">{error ?? "Location not found"}</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-lg px-5 py-10">
      <Link href="/settings/locations" className="text-sm text-amber-100/50 hover:text-amber-50">
        ← Locations
      </Link>
      <p className="mt-4 font-display text-4xl text-amber-50">{location.name}</p>

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
        <label className="flex items-center gap-2 text-sm text-amber-100/70">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="rounded border-amber-200/20"
          />
          Location is active
        </label>
        <Button type="submit" disabled={saving}>
          {saving ? "Saving…" : "Save location"}
        </Button>
      </form>

      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
    </main>
  );
}
