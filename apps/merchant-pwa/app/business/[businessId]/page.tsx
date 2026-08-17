"use client";

import Link from "next/link";
import { useParams } from "next/navigation";
import { useEffect, useState } from "react";

import type { Business } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import { Card } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export default function BusinessDashboardPage() {
  const params = useParams<{ businessId: string }>();
  const businessId = params.businessId;

  const [business, setBusiness] = useState<Business | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    session.setActiveBusinessId(businessId);
    getApiClient()
      .getBusiness(businessId)
      .then(setBusiness)
      .catch((err) =>
        setError(err instanceof ApiError ? err.message : "Failed to load store"),
      );
  }, [businessId]);

  return (
    <div className="space-y-4">
      <Link href="/businesses" className="text-xs text-amber-300/70 hover:text-amber-100">
        ← Stores
      </Link>
      <h1 className="text-2xl font-semibold">{business?.name ?? "Store"}</h1>
      {business ? (
        <p className="text-sm text-amber-200/70">
          {business.type} · {business.status}
        </p>
      ) : null}
      {error ? <p className="text-sm text-red-300">{error}</p> : null}

      <div className="grid gap-3 sm:grid-cols-2">
        <Link href={`/business/${businessId}/orders`}>
          <Card className="transition-colors hover:border-emerald-500/50">
            <p className="font-medium">Orders</p>
            <p className="text-sm text-amber-200/70">Accept and progress incoming orders</p>
          </Card>
        </Link>
        <Link href={`/business/${businessId}/catalog`}>
          <Card className="transition-colors hover:border-emerald-500/50">
            <p className="font-medium">Catalog</p>
            <p className="text-sm text-amber-200/70">Products and variants</p>
          </Card>
        </Link>
      </div>
    </div>
  );
}
