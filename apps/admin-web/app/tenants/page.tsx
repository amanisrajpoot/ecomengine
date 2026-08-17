"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { Tenant } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Button, Card, Input } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export default function TenantsPage() {
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [name, setName] = useState("");
  const [slug, setSlug] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        if (!session.getAccessToken()) {
          setError("Sign in as super admin.");
          return;
        }
        const list = await getApiClient().listTenants();
        setTenants(list);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load tenants");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function createTenant(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      const tenant = await getApiClient().createTenant({ name, slug });
      setTenants((prev) => [tenant, ...prev]);
      setName("");
      setSlug("");
      session.setTenantId(tenant.id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create tenant");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Tenants</h1>
      {loading ? <p className="text-sm text-violet-200/60">Loading…</p> : null}
      {error ? (
        <p className="text-sm text-red-300">
          {error} <Link href="/login" className="underline">Sign in</Link>
        </p>
      ) : null}

      <ul className="space-y-2">
        {tenants.map((tenant) => (
          <li key={tenant.id}>
            <Card>
              <p className="font-medium">{tenant.name}</p>
              <p className="text-xs text-violet-300/70">{tenant.slug}</p>
              <p className="font-mono text-xs text-violet-400/50">{tenant.id}</p>
              <Button
                variant="ghost"
                className="mt-2"
                onClick={() => {
                  session.setTenantId(tenant.id);
                }}
              >
                Use as tenant context
              </Button>
            </Card>
          </li>
        ))}
      </ul>

      <Card title="Create tenant">
        <form className="space-y-3" onSubmit={createTenant}>
          <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} required />
          <Input label="Slug" value={slug} onChange={(e) => setSlug(e.target.value)} required />
          <Button type="submit" disabled={creating}>Create</Button>
        </form>
      </Card>
    </div>
  );
}
