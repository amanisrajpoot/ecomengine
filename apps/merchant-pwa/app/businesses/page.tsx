"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import type { Business, BusinessType } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Badge, Button, Card, EmptyState, Input, Skeleton } from "@commerce/ui";

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
  const [showCreate, setShowCreate] = useState(false);

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
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-bold text-gray-900">My stores</h1>
        <p className="text-sm text-gray-500">Select a store to manage orders and menu.</p>
      </div>

      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-20" />
          <Skeleton className="h-20" />
        </div>
      ) : null}

      {error ? (
        <p className="text-sm text-red-600">
          {error}{" "}
          <Link href="/login" className="font-medium underline">Sign in</Link>
        </p>
      ) : null}

      <ul className="space-y-3">
        {businesses.map((b) => (
          <li key={b.id}>
            <Link
              href={`/business/${b.id}`}
              onClick={() => session.setActiveBusinessId(b.id)}
              className="block rounded-2xl border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md"
            >
              <div className="flex items-center justify-between gap-3">
                <div>
                  <p className="font-semibold text-gray-900">{b.name}</p>
                  <p className="mt-1 text-xs text-gray-500">{b.type}</p>
                </div>
                <Badge variant={b.status === "ACTIVE" ? "accent" : "muted"}>{b.status}</Badge>
              </div>
            </Link>
          </li>
        ))}
      </ul>

      {!loading && businesses.length === 0 && !error ? (
        <EmptyState
          title="No stores yet"
          description="Create your first store to start accepting orders."
          action={
            <Button variant="brand" onClick={() => setShowCreate(true)}>
              Create store
            </Button>
          }
        />
      ) : null}

      {showCreate || businesses.length > 0 ? (
        <Card variant="light" title={businesses.length ? "Add store" : "Create store"}>
          <form className="space-y-3" onSubmit={createStore}>
            <Input
              variant="light"
              label="Store name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
            <label className="flex flex-col gap-1.5 text-sm">
              <span className="text-gray-600">Type</span>
              <select
                className="rounded-lg border border-gray-300 bg-white px-3 py-2 text-gray-900 focus:border-orange-500 focus:outline-none focus:ring-1 focus:ring-orange-500/40"
                value={type}
                onChange={(e) => setType(e.target.value as BusinessType)}
              >
                {BUSINESS_TYPES.map((t) => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </label>
            <Button type="submit" variant="brand" disabled={creating || !name.trim()}>
              {creating ? "Creating…" : "Create store"}
            </Button>
          </form>
        </Card>
      ) : null}
    </div>
  );
}
