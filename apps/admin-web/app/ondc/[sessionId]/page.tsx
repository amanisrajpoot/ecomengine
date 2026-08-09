"use client";

import { ApiError } from "@commerce/api-client";
import type { OndcSession } from "@commerce/types";
import { OndcSessionCard, Spinner, StatusBadge } from "@commerce/ui";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { JsonBlock } from "../../../components/JsonBlock";
import { api, getTenantId, getToken } from "../../../lib/session";

export default function OndcSessionPage() {
  const router = useRouter();
  const params = useParams<{ sessionId: string }>();
  const [session, setSession] = useState<OndcSession | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

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
        const data = await api().getOndcSession(params.sessionId);
        if (!cancelled) setSession(data);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "ONDC session not found");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [params.sessionId, router]);

  return (
    <main className="mx-auto max-w-4xl px-5 py-10">
      <Link href="/ondc" className="text-sm text-violet-300/70 hover:text-violet-100">
        ← ONDC
      </Link>
      <p className="mt-4 font-display text-4xl text-violet-50">ONDC session</p>
      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-violet-300" />
        </div>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      {session ? (
        <div className="mt-8 space-y-6">
          <OndcSessionCard session={session} />
          <div className="rounded-2xl border border-violet-200/10 px-4 py-4 text-sm text-violet-100/70">
            <div className="flex flex-wrap items-center gap-2">
              <StatusBadge status={session.stage} />
              <span className="font-mono text-violet-50">{session.transaction_id}</span>
            </div>
            <p className="mt-3">
              BAP <span className="text-violet-50">{session.bap_id}</span> →{" "}
              <span className="break-all text-violet-100/55">{session.bap_uri}</span>
            </p>
            <p className="mt-2">
              BPP <span className="text-violet-50">{session.bpp_id}</span>
            </p>
            {session.order_id ? (
              <p className="mt-3">
                Internal order{" "}
                <Link
                  href={`/orders/${session.order_id}/debugger`}
                  className="text-violet-300 hover:text-violet-100"
                >
                  {session.order_id}
                </Link>
              </p>
            ) : null}
            {session.cart_id ? (
              <p className="mt-1 text-xs text-violet-100/45">Cart {session.cart_id}</p>
            ) : null}
          </div>
          <JsonBlock title="Selected items" data={session.selected_items} defaultOpen />
          <JsonBlock title="Callback log" data={session.callback_log} defaultOpen />
          <JsonBlock title="Beckn context" data={session.context_json} />
        </div>
      ) : null}
    </main>
  );
}
