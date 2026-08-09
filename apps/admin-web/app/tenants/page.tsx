"use client";

import { ApiError } from "@commerce/api-client";
import type { Tenant } from "@commerce/types";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, getToken, setTenantId } from "../../lib/session";

export default function TenantsPage() {
  const router = useRouter();
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const rows = await api().listTenants();
        if (!cancelled) setTenants(rows);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load tenants");
        }
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router]);

  return (
    <main className="mx-auto max-w-4xl px-5 py-10">
      <p className="font-display text-4xl text-violet-50">Tenants</p>
      <p className="mt-2 text-sm text-violet-100/55">
        Select a tenant to set order debugger context (stored in browser).
      </p>
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      <ul className="mt-8 flex flex-col gap-2">
        {tenants.map((tenant) => (
          <li key={tenant.id}>
            <button
              type="button"
              className="w-full rounded-2xl border border-violet-200/10 bg-violet-950/25 px-5 py-4 text-left transition hover:border-violet-300/25"
              onClick={() => {
                setTenantId(tenant.id);
                router.push("/orders");
              }}
            >
              <p className="font-medium text-violet-50">{tenant.name}</p>
              <p className="text-xs text-violet-100/50">
                {tenant.slug} · {tenant.status} · {tenant.id}
              </p>
            </button>
          </li>
        ))}
      </ul>
      {!error && tenants.length === 0 ? (
        <p className="mt-8 text-sm text-violet-100/55">No tenants visible for this account.</p>
      ) : null}
    </main>
  );
}
