"use client";

import { ApiError } from "@commerce/api-client";
import { Button, TextField } from "@commerce/ui";
import { useRouter } from "next/navigation";
import { FormEvent, useState } from "react";

import { api, getTenantId, setSession } from "../../lib/session";

export default function LoginPage() {
  const router = useRouter();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [tenantId, setTenantId] = useState(getTenantId() ?? "");
  const [email, setEmail] = useState("customer@demo.com");
  const [password, setPassword] = useState("Demo123!");
  const [displayName, setDisplayName] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    if (!tenantId.trim()) {
      setError("Tenant ID is required for customer sessions.");
      return;
    }
    setBusy(true);
    try {
      localStorage.setItem("ce_customer_tenant", tenantId.trim());
      const client = api();
      const token =
        mode === "login"
          ? await client.login({ email, password })
          : await client.register({
              email,
              password,
              display_name: displayName || undefined,
            });
      setSession(token.access_token, tenantId.trim());
      router.push("/browse");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not sign in");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="mx-auto flex min-h-[calc(100vh-4rem)] max-w-md flex-col justify-center px-5 py-12">
      <p className="font-display text-4xl text-emerald-50">Commerce</p>
      <h1 className="mt-3 text-xl text-emerald-50/90">
        {mode === "login" ? "Sign in to order" : "Create a customer account"}
      </h1>
      <form onSubmit={onSubmit} className="mt-8 flex flex-col gap-4">
        <TextField
          label="Tenant ID"
          value={tenantId}
          onChange={(e) => setTenantId(e.target.value)}
          placeholder="UUID from your environment"
          required
        />
        {mode === "register" ? (
          <TextField
            label="Display name"
            value={displayName}
            onChange={(e) => setDisplayName(e.target.value)}
          />
        ) : null}
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
          minLength={8}
        />
        {error ? <p className="text-sm text-rose-300">{error}</p> : null}
        <Button type="submit" disabled={busy}>
          {busy ? "Working…" : mode === "login" ? "Sign in" : "Register"}
        </Button>
      </form>
      <button
        type="button"
        className="mt-4 text-left text-sm text-emerald-100/55 hover:text-emerald-50"
        onClick={() => setMode(mode === "login" ? "register" : "login")}
      >
        {mode === "login" ? "Need an account? Register" : "Have an account? Sign in"}
      </button>
    </main>
  );
}
