"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { Business } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Card } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export default function BusinessesPage() {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        if (!session.getAccessToken()) {
          setError("Sign in to browse businesses.");
          setBusinesses([]);
          return;
        }
        const list = await getApiClient().listBusinesses({ status: "ACTIVE" });
        setBusinesses(list);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load businesses");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Businesses</h1>
        <p className="text-sm text-emerald-200/70">Active stores and services in your tenant.</p>
      </div>

      {loading ? <p className="text-sm text-emerald-200/60">Loading…</p> : null}
      {error ? (
        <p className="text-sm text-red-300">
          {error}{" "}
          {!session.getAccessToken() ? (
            <Link href="/login" className="underline">Sign in</Link>
          ) : null}
        </p>
      ) : null}

      <ul className="space-y-3">
        {businesses.map((business) => (
          <li key={business.id}>
            <Link href={`/business/${business.id}`}>
              <Card className="transition-colors hover:border-emerald-500/50">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-medium text-emerald-50">{business.name}</p>
                    <p className="text-xs uppercase tracking-wide text-emerald-400/80">
                      {business.type}
                    </p>
                    {business.description ? (
                      <p className="mt-1 text-sm text-emerald-200/70">{business.description}</p>
                    ) : null}
                  </div>
                  <span className="text-xs text-emerald-300/60">Open →</span>
                </div>
              </Card>
            </Link>
          </li>
        ))}
      </ul>

      {!loading && !error && businesses.length === 0 ? (
        <p className="text-sm text-emerald-200/60">No active businesses yet.</p>
      ) : null}
    </div>
  );
}
