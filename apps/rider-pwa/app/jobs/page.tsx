"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import type { Delivery } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Card } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export default function JobsPage() {
  const [deliveries, setDeliveries] = useState<Delivery[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        if (!session.getAccessToken()) {
          setError("Sign in to view jobs.");
          return;
        }
        const list = await getApiClient().listMyDeliveries(true);
        setDeliveries(list);
      } catch (err) {
        if (err instanceof ApiError && err.code === "PARTNER_NOT_FOUND") {
          setError("Create your partner profile first.");
        } else {
          setError(err instanceof ApiError ? err.message : "Failed to load jobs");
        }
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Active jobs</h1>
      <p className="text-sm text-sky-200/70">Deliveries assigned to you.</p>
      {loading ? <p className="text-sm text-sky-200/60">Loading…</p> : null}
      {error ? (
        <p className="text-sm text-red-300">
          {error}{" "}
          <Link href="/onboarding" className="underline">Partner profile</Link>
          {" · "}
          <Link href="/login" className="underline">Sign in</Link>
        </p>
      ) : null}

      <ul className="space-y-2">
        {deliveries.map((delivery) => (
          <li key={delivery.id}>
            <Link href={`/jobs/${delivery.id}`}>
              <Card className="transition-colors hover:border-emerald-500/50">
                <div className="flex justify-between gap-3">
                  <div>
                    <p className="font-medium">{delivery.status}</p>
                    <p className="font-mono text-xs text-sky-300/60">{delivery.id.slice(0, 8)}…</p>
                    <p className="text-xs text-sky-200/60">
                      {delivery.stops?.length ?? 0} stops
                    </p>
                  </div>
                  <span className="text-xs text-sky-300/60">Open →</span>
                </div>
              </Card>
            </Link>
          </li>
        ))}
      </ul>

      {!loading && !error && deliveries.length === 0 ? (
        <p className="text-sm text-sky-200/60">
          No active jobs. Stay online on your{" "}
          <Link href="/onboarding" className="underline">profile</Link> page.
        </p>
      ) : null}
    </div>
  );
}
