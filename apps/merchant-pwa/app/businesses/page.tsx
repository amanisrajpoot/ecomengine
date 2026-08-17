"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import type { Business, BusinessType } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Button, Card, Input } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

const BUSINESS_TYPES: BusinessType[] = ["FOOD", "GROCERY", "RETAIL", "COURIER"];

export default function BusinessesPage() {
  const router = useRouter();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [name, setName] = useState("");
  const [type, setType] = useState<BusinessType>("FOOD");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        if (!session.getAccessToken()) {
          setError("Sign in to manage stores.");
          return;
        }
        const list = await getApiClient().listBusinesses();
        setBusinesses(list);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load stores");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  async function createStore(e: React.FormEvent) {
    e.preventDefault();
    setCreating(true);
    setError(null);
    try {
      const business = await getApiClient().createBusiness({ name, type });
      session.setActiveBusinessId(business.id);
      router.push(`/business/${business.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create store");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">My stores</h1>
      {loading ? <p className="text-sm text-amber-200/60">Loading…</p> : null}
      {error ? (
        <p className="text-sm text-red-300">
          {error}{" "}
          <Link href="/login" className="underline">Sign in</Link>
        </p>
      ) : null}

      <ul className="space-y-2">
        {businesses.map((b) => (
          <li key={b.id}>
            <Link href={`/business/${b.id}`} onClick={() => session.setActiveBusinessId(b.id)}>
              <Card className="transition-colors hover:border-emerald-500/50">
                <p className="font-medium">{b.name}</p>
                <p className="text-xs uppercase text-amber-300/70">{b.type} · {b.status}</p>
              </Card>
            </Link>
          </li>
        ))}
      </ul>

      <Card title="Create store">
        <form className="space-y-3" onSubmit={createStore}>
          <Input label="Store name" value={name} onChange={(e) => setName(e.target.value)} required />
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="text-emerald-200/80">Type</span>
            <select
              className="rounded-lg border border-emerald-700/40 bg-emerald-950/60 px-3 py-2"
              value={type}
              onChange={(e) => setType(e.target.value as BusinessType)}
            >
              {BUSINESS_TYPES.map((t) => (
                <option key={t} value={t}>{t}</option>
              ))}
            </select>
          </label>
          <Button type="submit" disabled={creating || !name.trim()}>
            {creating ? "Creating…" : "Create store"}
          </Button>
        </form>
      </Card>
    </div>
  );
}
