"use client";

import { ApiError } from "@commerce/api-client";
import type { Business, StaffMember } from "@commerce/types";
import { Button, EmptyState, Spinner, StaffCard, TextField, useToast } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { api, getBusinessId, getToken, setBusinessId } from "../../../lib/session";

export default function StaffSettingsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(getBusinessId());
  const [staff, setStaff] = useState<StaffMember[]>([]);
  const [email, setEmail] = useState("");
  const [role, setRole] = useState<"STAFF" | "BUSINESS_MANAGER">("STAFF");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const loadStaff = useCallback(async (businessId: string) => {
    const rows = await api().listBusinessStaff(businessId);
    setStaff(rows);
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
        if (current) await loadStaff(current);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load staff");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [loadStaff, router, selectedId]);

  async function onBusinessChange(id: string) {
    setSelectedId(id);
    setBusinessId(id);
    setLoading(true);
    setError(null);
    try {
      await loadStaff(id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load staff");
    } finally {
      setLoading(false);
    }
  }

  async function onAssign(event: React.FormEvent) {
    event.preventDefault();
    if (!selectedId) return;
    if (!email.trim()) {
      setError("Email is required.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      await api().assignBusinessStaff(selectedId, {
        email: email.trim(),
        role,
      });
      toast({ title: "Staff member added", variant: "success" });
      setEmail("");
      await loadStaff(selectedId);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to assign staff");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <Link href="/settings" className="text-sm text-amber-100/50 hover:text-amber-50">
        ← Settings
      </Link>
      <p className="mt-4 font-display text-4xl text-amber-50">Staff</p>
      <p className="mt-2 text-sm text-amber-100/55">
        Invite team members by email. They must already have an account in your tenant.
      </p>

      <label className="mt-6 flex max-w-md flex-col gap-1.5 text-sm text-amber-50/80">
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

      <form
        onSubmit={(e) => void onAssign(e)}
        className="mt-8 rounded-2xl border border-amber-200/10 bg-amber-950/25 p-5"
      >
        <p className="font-medium text-amber-50">Add team member</p>
        <p className="mt-1 text-sm text-amber-100/50">
          Only business owners can assign roles. Managers can view the list.
        </p>
        <div className="mt-4 grid gap-4 sm:grid-cols-2">
          <TextField
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="staff@example.com"
            disabled={busy}
          />
          <label className="flex flex-col gap-1.5 text-sm text-amber-50/80">
            <span>Role</span>
            <select
              className="rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
              value={role}
              onChange={(e) => setRole(e.target.value as "STAFF" | "BUSINESS_MANAGER")}
              disabled={busy}
            >
              <option value="STAFF">Staff</option>
              <option value="BUSINESS_MANAGER">Manager</option>
            </select>
          </label>
        </div>
        <div className="mt-4">
          <Button type="submit" disabled={busy || !selectedId}>
            {busy ? "Adding…" : "Add staff"}
          </Button>
        </div>
      </form>

      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-amber-300" />
        </div>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      {!loading ? (
        <ul className="mt-8 flex flex-col gap-3">
          {staff.map((member) => (
            <li key={member.binding_id}>
              <StaffCard
                member={member}
                className="!border-amber-200/10 !bg-amber-950/25"
              />
            </li>
          ))}
        </ul>
      ) : null}

      {!loading && !error && staff.length === 0 ? (
        <EmptyState
          className="mt-8 border-amber-200/15"
          title="No staff yet"
          description="Add a team member by email once they have registered in your tenant."
        />
      ) : null}
    </main>
  );
}
