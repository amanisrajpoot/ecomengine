"use client";

import { ApiError } from "@commerce/api-client";
import { Button, TextField } from "@commerce/ui";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { api, getTenantId, setSession } from "../../lib/session";

export default function LoginPage() {
  const router = useRouter();
  const [tenantId, setTenantId] = useState(getTenantId() ?? "");
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("ChangeMe123!");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setBusy(true);
    try {
      const token = await api().login({ email, password });
      setSession(token.access_token, tenantId.trim() || null);
      router.push("/orders");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Sign in failed");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-md flex-col justify-center px-5 py-12">
      <p className="font-display text-4xl text-violet-50">Admin</p>
      <h1 className="mt-3 text-xl text-violet-50/90">Platform sign in</h1>
      <p className="mt-2 text-sm text-violet-100/50">
        Super admin can omit tenant ID for tenant list; set tenant for order debugger.
      </p>
      <form onSubmit={onSubmit} className="mt-8 flex flex-col gap-4">
        <TextField
          label="Tenant ID (optional for super admin)"
          value={tenantId}
          onChange={(e) => setTenantId(e.target.value)}
          placeholder="UUID for order/ledger scope"
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
        <Button
          type="submit"
          disabled={busy}
          className="bg-violet-500 text-violet-50 hover:bg-violet-400"
        >
          {busy ? "Signing in…" : "Sign in"}
        </Button>
      </form>
    </main>
  );
}
