"use client";

import { ApiError } from "@commerce/api-client";
import type { Business } from "@commerce/types";
import { Button, Spinner, TextField, useToast } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { capabilityLabels } from "../../../lib/settings-helpers";
import { api, getBusinessId, getToken, setBusinessId } from "../../../lib/session";

export default function BusinessSettingsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(getBusinessId());
  const [business, setBusiness] = useState<Business | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [phone, setPhone] = useState("");
  const [email, setEmail] = useState("");
  const [prepMinutes, setPrepMinutes] = useState("20");
  const [status, setStatus] = useState("ACTIVE");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  const loadBusiness = useCallback(async (businessId: string) => {
    const row = await api().getBusiness(businessId);
    setBusiness(row);
    setName(row.name);
    setDescription(row.description ?? "");
    setPhone(row.contact?.phone ?? "");
    setEmail(row.contact?.email ?? "");
    setPrepMinutes(String(row.settings?.preparation_time_minutes ?? 20));
    setStatus(row.status);
  }, []);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const rows = await api().listBusinesses();
        if (cancelled) return;
        setBusinesses(rows);
        const current =
          selectedId && rows.some((row) => row.id === selectedId)
            ? selectedId
            : rows[0]?.id ?? null;
        if (current && current !== selectedId) {
          setSelectedId(current);
          setBusinessId(current);
        }
        if (current) await loadBusiness(current);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load business");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [loadBusiness, router, selectedId]);

  async function onBusinessChange(id: string) {
    setSelectedId(id);
    setBusinessId(id);
    setLoading(true);
    setError(null);
    try {
      await loadBusiness(id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load business");
    } finally {
      setLoading(false);
    }
  }

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!selectedId) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await api().updateBusiness(selectedId, {
        name: name.trim(),
        description: description.trim() || null,
        contact: { phone: phone.trim() || null, email: email.trim() || null },
        settings: {
          preparation_time_minutes: Number.parseInt(prepMinutes, 10) || 0,
        },
        status,
      });
      setBusiness(updated);
      toast({ title: "Business updated", variant: "success" });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  return (
    <main className="mx-auto max-w-lg px-5 py-10">
      <Link href="/settings" className="text-sm text-amber-100/50 hover:text-amber-50">
        ← Settings
      </Link>
      <p className="mt-4 font-display text-4xl text-amber-50">Business profile</p>

      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-amber-300" />
        </div>
      ) : (
        <>
          <label className="mt-6 flex flex-col gap-1.5 text-sm text-amber-50/80">
            <span>Business</span>
            <select
              className="rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
              value={selectedId ?? ""}
              onChange={(e) => void onBusinessChange(e.target.value)}
            >
              {businesses.map((row) => (
                <option key={row.id} value={row.id}>
                  {row.name} ({row.type})
                </option>
              ))}
            </select>
          </label>

          {business ? (
            <p className="mt-3 text-xs text-amber-100/45">
              Capabilities: {capabilityLabels(business.capabilities).join(", ") || "none"}
            </p>
          ) : null}

          <form className="mt-8 flex flex-col gap-4" onSubmit={onSubmit}>
            <TextField
              label="Display name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
            />
            <label className="flex flex-col gap-1.5 text-sm text-amber-50/80">
              <span>Description</span>
              <textarea
                className="min-h-20 rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </label>
            <TextField
              label="Phone"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
            />
            <TextField
              label="Email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
            />
            <TextField
              label="Prep time (minutes)"
              type="number"
              min="0"
              value={prepMinutes}
              onChange={(e) => setPrepMinutes(e.target.value)}
              className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
            />
            <label className="flex flex-col gap-1.5 text-sm text-amber-50/80">
              <span>Status</span>
              <select
                className="rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="ACTIVE">Active — accepting orders</option>
                <option value="PAUSED">Paused — hidden from customers</option>
              </select>
            </label>
            <Button type="submit" disabled={saving}>
              {saving ? "Saving…" : "Save changes"}
            </Button>
          </form>
        </>
      )}

      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
    </main>
  );
}
