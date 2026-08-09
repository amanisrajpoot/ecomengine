"use client";

import { ApiError } from "@commerce/api-client";
import { Button, TextField } from "@commerce/ui";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { api, getTenantId, setSession } from "../../lib/session";

export default function LoginPage() {
  const router = useRouter();
  const [tenantId, setTenantId] = useState(getTenantId() ?? "");
  const [email, setEmail] = useState("rider@demo.com");
  const [password, setPassword] = useState("Demo123!");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!tenantId.trim()) {
      setError("Tenant ID is required.");
      return;
    }
    setBusy(true);
    try {
      localStorage.setItem("ce_rider_tenant", tenantId.trim());
      const token = await api().login({ email, password });
      setSession(token.access_token, tenantId.trim());
      await api().getMyPartner();
      router.push("/deliveries");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : "Sign in failed — ensure a delivery partner profile exists for this user",
      );
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-md flex-col justify-center px-5 py-12">
      <p className="font-display text-4xl text-sky-50">Rider</p>
      <h1 className="mt-3 text-xl text-sky-50/90">Partner sign in</h1>
      <form onSubmit={onSubmit} className="mt-8 flex flex-col gap-4">
        <TextField
          label="Tenant ID"
          value={tenantId}
          onChange={(e) => setTenantId(e.target.value)}
          required
        />
        <TextField
          label="Email"
          type="email"
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          required
        />
        <TextField
          label="Password"
          type="password"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          required
        />
        {error ? <p className="text-sm text-rose-300">{error}</p> : null}
        <Button type="submit" disabled={busy} className="bg-sky-500 text-sky-950 hover:bg-sky-400">
          {busy ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </main>
  );
}
