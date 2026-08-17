"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { DeliveryPartnerProfile, Vehicle } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Badge, Button, Card, Input, StatTile } from "@commerce/ui";

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

  async function goOffline() {
    setError(null);
    try {
      const p = await getApiClient().updatePartnerProfile({ is_online: false });
      setProfile(p);
      setMessage("You are offline.");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not go offline");
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
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">Partner profile</h1>
        <p className="text-sm text-gray-500">Go online to receive delivery assignments.</p>
      </div>

      {loading ? <p className="text-sm text-gray-500">Loading…</p> : null}
      {error ? (
        <p className="text-sm text-red-600">
          {error}{" "}
          <Link href="/login" className="font-medium underline">Sign in</Link>
        </p>
      ) : null}
      {message ? <p className="text-sm text-emerald-600">{message}</p> : null}

      {profile ? (
        <div className="grid grid-cols-2 gap-3">
          <StatTile
            label="Status"
            value={profile.is_online ? "Online" : "Offline"}
            accent={profile.is_online}
            className={profile.is_online ? "border-blue-200 bg-blue-50" : ""}
          />
          <StatTile label="Vehicles" value={vehicles.length} />
        </div>
      ) : null}

      {!profile ? (
        <Card variant="light" title="Create profile">
          <p className="mb-3 text-sm text-gray-500">
            Requires <code className="text-xs">DELIVERY_PARTNER</code> role on your account.
          </p>
          <Button variant="brand" className="bg-[var(--brand)] hover:bg-[var(--brand-dark)]" onClick={createProfile}>
            Create partner profile
          </Button>
        </Card>
      ) : (
        <Card variant="light" title="Availability">
          <p className="text-sm text-gray-600">
            {profile.is_online
              ? "You are visible to dispatch for new assignments."
              : "Go online with your current GPS coordinates."}
          </p>
          <div className="mt-3 grid gap-3 sm:grid-cols-2">
            <Input variant="light" label="Latitude" value={lat} onChange={(e) => setLat(e.target.value)} />
            <Input variant="light" label="Longitude" value={lng} onChange={(e) => setLng(e.target.value)} />
          </div>
          <div className="mt-3 flex flex-wrap gap-2">
            <Button
              variant="brand"
              className="bg-[var(--brand)] hover:bg-[var(--brand-dark)]"
              onClick={goOnline}
            >
              Go online
            </Button>
            {profile.is_online ? (
              <Button
                variant="secondary"
                className="border-gray-300 bg-gray-100 text-gray-800 hover:bg-gray-200"
                onClick={goOffline}
              >
                Go offline
              </Button>
            ) : null}
          </div>
        </Card>
      )}

      <Card variant="light" title="Vehicles">
        {vehicles.length === 0 ? (
          <p className="text-sm text-gray-500">No vehicles registered yet.</p>
        ) : (
          <ul className="mb-3 divide-y divide-gray-100">
            {vehicles.map((v) => (
              <li key={v.id} className="flex items-center justify-between py-2 text-sm first:pt-0">
                <span className="font-medium text-gray-900">{v.vehicle_type}</span>
                {v.registration ? (
                  <Badge variant="muted">{v.registration}</Badge>
                ) : (
                  <Badge variant="muted">No reg</Badge>
                )}
              </li>
            ))}
          </ul>
        )}
        <form className="space-y-3" onSubmit={registerVehicle}>
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="text-gray-600">Vehicle type</span>
            <select
              className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500/40"
              value={vehicleType}
              onChange={(e) => setVehicleType(e.target.value)}
            >
              <option value="BIKE">BIKE</option>
              <option value="CAR">CAR</option>
              <option value="VAN">VAN</option>
            </select>
          </label>
          <Input
            variant="light"
            label="Registration (optional)"
            value={registration}
            onChange={(e) => setRegistration(e.target.value)}
          />
          <Button
            type="submit"
            variant="secondary"
            className="border-gray-300 bg-gray-100 text-gray-800 hover:bg-gray-200"
          >
            Add vehicle
          </Button>
        </form>
      </Card>
    </div>
  );
}
