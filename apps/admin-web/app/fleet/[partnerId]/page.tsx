"use client";

import { ApiError } from "@commerce/api-client";
import type { Partner, Vehicle } from "@commerce/types";
import { Button, PartnerCard, Spinner, TextField, useToast } from "@commerce/ui";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, getToken } from "../../../lib/session";

const VEHICLE_TYPES = ["BIKE", "SCOOTER", "CAR", "VAN", "OTHER"] as const;

export default function FleetPartnerPage() {
  const router = useRouter();
  const params = useParams<{ partnerId: string }>();
  const { toast } = useToast();
  const [partner, setPartner] = useState<Partner | null>(null);
  const [vehicles, setVehicles] = useState<Vehicle[]>([]);
  const [displayName, setDisplayName] = useState("");
  const [status, setStatus] = useState("ACTIVE");
  const [vehicleType, setVehicleType] = useState<string>("BIKE");
  const [registration, setRegistration] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [addingVehicle, setAddingVehicle] = useState(false);

  const load = useCallback(async () => {
    const [row, vehicleRows] = await Promise.all([
      api().getDeliveryPartner(params.partnerId),
      api().listVehicles({ partner_id: params.partnerId }),
    ]);
    setPartner(row);
    setVehicles(vehicleRows);
    setDisplayName(row.display_name ?? "");
    setStatus(row.status);
  }, [params.partnerId]);

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
          setError(err instanceof ApiError ? err.message : "Failed to load partner");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [load, router]);

  async function onSave(event: React.FormEvent) {
    event.preventDefault();
    setSaving(true);
    setError(null);
    try {
      const updated = await api().updateDeliveryPartner(params.partnerId, {
        display_name: displayName.trim() || null,
        status,
      });
      setPartner(updated);
      toast({ title: "Partner updated", variant: "success" });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  async function onAddVehicle(event: React.FormEvent) {
    event.preventDefault();
    setAddingVehicle(true);
    setError(null);
    try {
      const row = await api().createVehicle({
        partner_id: params.partnerId,
        vehicle_type: vehicleType,
        registration: registration.trim() || null,
      });
      setVehicles((rows) => [...rows, row]);
      setRegistration("");
      toast({ title: "Vehicle added", variant: "success" });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add vehicle");
    } finally {
      setAddingVehicle(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto max-w-lg px-5 py-16">
        <Spinner size="lg" className="text-violet-300" />
      </main>
    );
  }

  if (!partner) {
    return (
      <main className="mx-auto max-w-lg px-5 py-10">
        <p className="text-rose-300">{error ?? "Partner not found"}</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-lg px-5 py-10">
      <Link href="/fleet" className="text-sm text-violet-100/50 hover:text-violet-50">
        ← Fleet
      </Link>
      <div className="mt-4">
        <PartnerCard
          partner={partner}
          subtitle={`User ${partner.user_id}`}
          className="!border-violet-200/10 !bg-violet-950/25"
        />
      </div>

      <form className="mt-8 flex flex-col gap-4" onSubmit={onSave}>
        <TextField
          label="Display name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          className="!border-violet-200/15 !bg-violet-950/40 !text-violet-50"
        />
        <label className="flex flex-col gap-1.5 text-sm text-violet-50/80">
          <span>Status</span>
          <select
            className="rounded-xl border border-violet-200/15 bg-violet-950/40 px-3 py-2.5 text-violet-50"
            value={status}
            onChange={(e) => setStatus(e.target.value)}
          >
            <option value="ACTIVE">Active</option>
            <option value="INACTIVE">Inactive</option>
            <option value="SUSPENDED">Suspended</option>
          </select>
        </label>
        <Button type="submit" disabled={saving}>
          {saving ? "Saving…" : "Save partner"}
        </Button>
      </form>

      <section className="mt-10">
        <h2 className="text-sm uppercase tracking-wide text-violet-200/50">Vehicles</h2>
        <ul className="mt-3 flex flex-col gap-2">
          {vehicles.map((vehicle) => (
            <li
              key={vehicle.id}
              className="rounded-xl border border-violet-200/10 bg-violet-950/20 px-4 py-3 text-sm text-violet-100/80"
            >
              {vehicle.vehicle_type}
              {vehicle.registration ? ` · ${vehicle.registration}` : ""}
              {!vehicle.is_active ? " (inactive)" : ""}
            </li>
          ))}
        </ul>

        <form
          className="mt-6 flex flex-col gap-3 rounded-2xl border border-violet-200/10 bg-violet-950/15 p-4"
          onSubmit={onAddVehicle}
        >
          <p className="text-sm font-medium text-violet-50/80">Add vehicle</p>
          <label className="flex flex-col gap-1.5 text-sm text-violet-50/80">
            <span>Type</span>
            <select
              className="rounded-xl border border-violet-200/15 bg-violet-950/40 px-3 py-2.5 text-violet-50"
              value={vehicleType}
              onChange={(e) => setVehicleType(e.target.value)}
            >
              {VEHICLE_TYPES.map((type) => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </label>
          <TextField
            label="Registration (optional)"
            value={registration}
            onChange={(e) => setRegistration(e.target.value)}
            className="!border-violet-200/15 !bg-violet-950/40 !text-violet-50"
          />
          <Button type="submit" variant="soft" disabled={addingVehicle}>
            {addingVehicle ? "Adding…" : "Add vehicle"}
          </Button>
        </form>
      </section>

      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
    </main>
  );
}
