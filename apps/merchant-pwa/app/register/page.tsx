"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError } from "@commerce/api-client";
import { Button, Card, Input } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [tenantId, setTenantId] = useState(session.getTenantId() ?? "");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      if (!tenantId.trim()) throw new Error("Tenant ID is required.");
      session.setTenantId(tenantId.trim());
      const token = await getApiClient().register({
        email,
        password,
        display_name: displayName || undefined,
      });
      session.setAccessToken(token.access_token);
      router.push("/businesses");
    } catch (err) {
      setError(
        err instanceof ApiError
          ? err.message
          : err instanceof Error
            ? err.message
            : "Registration failed",
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="mx-auto max-w-md space-y-4">
      <h1 className="text-2xl font-semibold">Merchant register</h1>
      <Card>
        <form className="space-y-3" onSubmit={onSubmit}>
          <Input label="Tenant ID" value={tenantId} onChange={(e) => setTenantId(e.target.value)} required />
          <Input label="Display name" value={displayName} onChange={(e) => setDisplayName(e.target.value)} />
          <Input label="Email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
          <Input
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
          />
          <Button type="submit" disabled={loading} className="w-full">
            {loading ? "Creating…" : "Register"}
          </Button>
        </form>
      </Card>
      <p className="text-sm text-amber-200/70">
        <Link href="/login" className="underline">Sign in</Link>
      </p>
      {error ? <p className="text-sm text-red-300">{error}</p> : null}
    </div>
  );
}
