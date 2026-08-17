"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError } from "@commerce/api-client";
import { Button, Card, Input } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("admin@example.com");
  const [password, setPassword] = useState("ChangeMe123!");
  const [tenantId, setTenantId] = useState(session.getTenantId() ?? "");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const trimmedTenant = tenantId.trim();
      session.setTenantId(trimmedTenant || null);
      const token = await getApiClient().login({ email, password });
      session.setAccessToken(token.access_token);
      if (token.tenant_id) {
        session.setTenantId(token.tenant_id);
      }
      router.push("/orders");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Login failed",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md space-y-4">
      <h1 className="text-2xl font-semibold">Admin sign in</h1>
      <Card>
        <form className="space-y-3" onSubmit={onSubmit}>
          <Input
            label="Tenant ID (optional for super admin)"
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
          />
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Signing in…" : "Sign in"}
          </Button>
        </form>
      </Card>
      {error ? <p className="text-sm text-red-300">{error}</p> : null}
    </div>
  );
}
