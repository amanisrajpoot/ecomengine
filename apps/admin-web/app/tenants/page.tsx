"use client";

import { ApiError } from "@commerce/api-client";
import type { Tenant } from "@commerce/types";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, getTenantId, getToken, setTenantId } from "../../lib/session";

export default function TenantsPage() {
  const router = useRouter();
  const [tenants, setTenants] = useState<Tenant[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const activeTenant = getTenantId();

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

  async function copyId(id: string) {
    try {
      await navigator.clipboard.writeText(id);
      setCopiedId(id);
      window.setTimeout(() => setCopiedId(null), 2000);
    } catch {
      setCopiedId(null);
    }
  }

  return (
    <main className="mx-auto max-w-4xl px-5 py-10">
      <p className="font-display text-4xl text-violet-50">Tenants</p>
      <p className="mt-2 text-sm text-violet-100/55">
        Select a tenant for order debugger context. Your choice is remembered in this browser.
      </p>
      {activeTenant ? (
        <p className="mt-3 rounded-xl border border-violet-300/20 bg-violet-500/10 px-4 py-2 text-sm text-violet-100/80">
          Active tenant: <code className="text-violet-50">{activeTenant}</code>
        </p>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      <ul className="mt-8 flex flex-col gap-2">
        {tenants.map((tenant) => (
          <li key={tenant.id}>
            <div className="flex flex-col gap-2 rounded-2xl border border-violet-200/10 bg-violet-950/25 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
              <button
                type="button"
                className="text-left transition hover:opacity-90"
                onClick={() => {
                  setTenantId(tenant.id);
                  router.push("/orders");
                }}
              >
                <p className="font-medium text-violet-50">{tenant.name}</p>
                <p className="text-xs text-violet-100/50">
                  {tenant.slug} · {tenant.status}
                </p>
              </button>
              <div className="flex flex-wrap items-center gap-2">
                <code className="max-w-xs truncate text-xs text-violet-200/60">{tenant.id}</code>
                <button
                  type="button"
                  className="rounded-lg border border-violet-200/15 px-2.5 py-1 text-xs text-violet-100/70 hover:bg-white/5"
                  onClick={() => copyId(tenant.id)}
                >
                  {copiedId === tenant.id ? "Copied" : "Copy ID"}
                </button>
                <button
                  type="button"
                  className="rounded-lg bg-violet-500/20 px-2.5 py-1 text-xs text-violet-100 hover:bg-violet-500/30"
                  onClick={() => {
                    setTenantId(tenant.id);
                    router.push("/orders");
                  }}
                >
                  Use for orders
                </button>
              </div>
            </div>
          </li>
        ))}
      </ul>
      {!error && tenants.length === 0 ? (
        <p className="mt-8 text-sm text-violet-100/55">No tenants visible for this account.</p>
      ) : null}
    </main>
  );
}
