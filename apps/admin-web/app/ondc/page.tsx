"use client";

import { ApiError } from "@commerce/api-client";
import type { OndcMeta, OndcSession } from "@commerce/types";
import { EmptyState, OndcSessionCard, Spinner } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { api, getTenantId, getToken } from "../../lib/session";

const STAGES = ["SEARCH", "SELECT", "INIT", "CONFIRM", "CANCEL"];

export default function OndcPage() {
  const router = useRouter();
  const [meta, setMeta] = useState<OndcMeta | null>(null);
  const [sessions, setSessions] = useState<OndcSession[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [stage, setStage] = useState("");

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    if (!getTenantId()) {
      setError("Select a tenant on the Tenants page first.");
      setLoading(false);
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const client = api();
        const [metaData, rows] = await Promise.all([
          client.getOndcMeta(),
          client.listOndcSessions({ stage: stage || undefined, limit: 100 }),
        ]);
        if (!cancelled) {
          setMeta(metaData);
          setSessions(rows);
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load ONDC sessions");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [router, stage]);

  return (
    <main className="mx-auto max-w-5xl px-5 py-10">
      <p className="font-display text-4xl text-violet-50">ONDC</p>
      <p className="mt-2 text-sm text-violet-100/55">
        BPP session log — Beckn transaction → cart/order linkage and callback payloads.
      </p>

      {meta ? (
        <div className="mt-6 rounded-2xl border border-violet-300/20 bg-violet-500/10 px-5 py-4 text-sm text-violet-100/70">
          <p>
            Adapter <span className="text-violet-50">{meta.adapter}</span> · v{meta.version} ·{" "}
            {meta.mock_mode ? "mock mode" : "production"} · domains{" "}
            {meta.supported_domains.join(", ")}
          </p>
        </div>
      ) : null}

      <label className="mt-6 flex max-w-xs flex-col gap-1.5 text-sm text-violet-50/80">
        <span>Stage</span>
        <select
          className="rounded-xl border border-violet-200/15 bg-violet-950/40 px-3 py-2.5 text-violet-50"
          value={stage}
          onChange={(e) => {
            setLoading(true);
            setStage(e.target.value);
          }}
        >
          <option value="">All</option>
          {STAGES.map((value) => (
            <option key={value} value={value}>
              {value}
            </option>
          ))}
        </select>
      </label>

      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-violet-300" />
        </div>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      <ul className="mt-8 flex flex-col gap-3">
        {sessions.map((session) => (
          <li key={session.id}>
            <Link href={`/ondc/${session.id}`}>
              <OndcSessionCard session={session} className="hover:border-violet-300/25" />
            </Link>
          </li>
        ))}
      </ul>

      {!loading && !error && sessions.length === 0 ? (
        <EmptyState
          className="mt-8 border-violet-200/15"
          title="No ONDC sessions"
          description="Run the Phase 20 golden test or POST to /integrations/ondc/search with X-Tenant-ID."
        />
      ) : null}
    </main>
  );
}
