"use client";

import { ApiError } from "@commerce/api-client";
import { Button, TextField, useToast } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, getTenantId, getToken } from "../../../lib/session";

export default function NewFleetPartnerPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [userId, setUserId] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!getToken()) router.replace("/login");
  }, [router]);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!getTenantId()) {
      setError("Select a tenant first.");
      return;
    }
    if (!userId.trim()) {
      setError("User ID is required.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const partner = await api().createDeliveryPartner({
        user_id: userId.trim(),
        display_name: displayName.trim() || null,
        status: "ACTIVE",
      });
      toast({ title: "Partner created", variant: "success" });
      router.push(`/fleet/${partner.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create partner");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto max-w-lg px-5 py-10">
      <Link href="/fleet" className="text-sm text-violet-100/50 hover:text-violet-50">
        ← Fleet
      </Link>
      <p className="mt-4 font-display text-4xl text-violet-50">Add delivery partner</p>
      <p className="mt-2 text-sm text-violet-100/55">
        Link an existing user ID (from demo.env or auth) to a rider profile.
      </p>

      <form className="mt-8 flex flex-col gap-4" onSubmit={onSubmit}>
        <TextField
          label="User ID (UUID)"
          value={userId}
          onChange={(e) => setUserId(e.target.value)}
          className="!border-violet-200/15 !bg-violet-950/40 !text-violet-50"
        />
        <TextField
          label="Display name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
          placeholder="e.g. Rajesh K"
          className="!border-violet-200/15 !bg-violet-950/40 !text-violet-50"
        />
        {error ? <p className="text-rose-300">{error}</p> : null}
        <Button type="submit" disabled={busy}>
          {busy ? "Creating…" : "Create partner"}
        </Button>
      </form>
    </main>
  );
}
