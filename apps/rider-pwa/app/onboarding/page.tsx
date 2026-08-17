"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { DeliveryPartnerProfile, Vehicle } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Button, Card, Input } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export default function OnboardingPage() {
  const [profile, setProfile] = useState<DeliveryPartnerProfile | null>(null);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [lat, setLat] = useState("12.9716");
  const [lng, setLng] = useState("77.5946");
  const [vehicleType, setVehicleType] = useState("BIKE");
  const [registration, setRegistration] = useState("");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  async function load() {
    setLoading(true);
    setError(null);
    try {
      if (!session.getAccessToken()) {
        setError("Sign in first.");
        return;
      }
      const api = getApiClient();
      try {
        const p = await api.getMyPartnerProfile();
        setProfile(p);
        if (p.current_lat) setLat(String(p.current_lat));
        if (p.current_lng) setLng(String(p.current_lng));
      } catch (err) {
        if (err instanceof ApiError && err.status === 404) {
          setProfile(null);
        } else {
          throw err;
        }
      }
      try {
        const v = await api.listMyVehicles();
        setVehicles(v);
      } catch {
        setVehicles([]);
      }
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load profile");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    load();
  }, []);

  async function createProfile() {
    setError(null);
    try {
      const p = await getApiClient().createPartnerProfile();
      setProfile(p);
      setMessage("Partner profile created.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create profile");
    }
  }

  async function goOnline() {
    setError(null);
    try {
      const latitude = Number(lat);
      const longitude = Number(lng);
      if (!Number.isFinite(latitude) || !Number.isFinite(longitude)) {
        throw new Error("Invalid coordinates.");
      }
      const p = await getApiClient().updatePartnerProfile({
        is_online: true,
        current_lat: latitude,
        current_lng: longitude,
      });
      setProfile(p);
      setMessage("You are online and visible for assignment.");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Could not go online",
      );
    }
  }

  async function registerVehicle(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    try {
      await getApiClient().createVehicle({
        vehicle_type: vehicleType,
        registration: registration || undefined,
      });
      setRegistration("");
      await load();
      setMessage("Vehicle registered.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not register vehicle");
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Partner profile</h1>
      {loading ? <p className="text-sm text-sky-200/60">Loading…</p> : null}
      {error ? (
        <p className="text-sm text-red-300">
          {error}{" "}
          <Link href="/login" className="underline">Sign in</Link>
        </p>
      ) : null}
      {message ? <p className="text-sm text-emerald-300">{message}</p> : null}

      {!profile ? (
        <Card title="Create profile">
          <p className="mb-3 text-sm text-sky-200/70">
            Requires <code>DELIVERY_PARTNER</code> role on your account.
          </p>
          <Button onClick={createProfile}>Create partner profile</Button>
        </Card>
      ) : (
        <Card title="Status">
          <p className="text-sm">
            Online: <strong>{profile.is_online ? "Yes" : "No"}</strong> · {profile.status}
          </p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <Input label="Latitude" value={lat} onChange={(e) => setLat(e.target.value)} />
            <Input label="Longitude" value={lng} onChange={(e) => setLng(e.target.value)} />
          </div>
          <Button className="mt-3" onClick={goOnline}>Go online</Button>
        </Card>
      )}

      <Card title="Vehicles">
        {vehicles.length === 0 ? (
          <p className="text-sm text-sky-200/60">No vehicles registered.</p>
        ) : (
          <ul className="mb-3 space-y-1 text-sm">
            {vehicles.map((v) => (
              <li key={v.id}>
                {v.vehicle_type}
                {v.registration ? ` · ${v.registration}` : ""}
              </li>
            ))}
          </ul>
        )}
        <form className="space-y-3" onSubmit={registerVehicle}>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="text-emerald-200/80">Vehicle type</span>
            <select
              className="rounded-lg border border-emerald-700/40 bg-emerald-950/60 px-3 py-2"
              value={vehicleType}
              onChange={(e) => setVehicleType(e.target.value)}
            >
              <option value="BIKE">BIKE</option>
              <option value="CAR">CAR</option>
              <option value="VAN">VAN</option>
            </select>
          </label>
          <Input
            label="Registration (optional)"
            value={registration}
            onChange={(e) => setRegistration(e.target.value)}
          />
          <Button type="submit" variant="secondary">Add vehicle</Button>
        </form>
      </Card>
    </div>
  );
}
