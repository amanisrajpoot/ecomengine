"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { api, getToken } from "../lib/session";

export default function HomePage() {
  const [meta, setMeta] = useState<{ name: string; version: string; environment: string } | null>(
    null,
  );

  useEffect(() => {
    if (!getToken()) return;
    api()
      .getMeta()
      .then(setMeta)
      .catch(() => setMeta(null));
  }, []);

  return (
    <main className="mx-auto max-w-4xl px-5 py-16">
      <p className="animate-rise font-display text-5xl text-violet-50 sm:text-6xl">Admin</p>
      <h1 className="animate-rise-delay mt-4 text-2xl font-medium text-violet-50/90">
        Platform ops & order debugger
      </h1>
      <p className="mt-4 max-w-lg text-violet-100/60">
        Trace the full chain — Order → Payment → Ledger → Fulfillment → Delivery → Settlement —
        across Food, Hyperlocal, and Courier verticals.
      </p>
      {meta ? (
        <p className="mt-4 text-sm text-violet-200/50">
          API {meta.name} v{meta.version} · {meta.environment}
        </p>
      ) : null}
      <div className="animate-rise-delay mt-8 flex flex-wrap gap-3">
        <Link
          href="/orders"
          className="rounded-xl bg-violet-500 px-5 py-3 text-sm font-semibold text-violet-50 hover:bg-violet-400"
        >
          Browse orders
        </Link>
        <Link
          href="/tenants"
          className="rounded-xl border border-violet-200/20 px-5 py-3 text-sm font-medium text-violet-50/90 hover:bg-white/5"
        >
          Tenants
        </Link>
        <Link
          href="/login"
          className="rounded-xl border border-violet-200/20 px-5 py-3 text-sm font-medium text-violet-50/90 hover:bg-white/5"
        >
          Sign in
        </Link>
      </div>
    </main>
  );
}
