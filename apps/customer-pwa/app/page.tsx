"use client";

import Link from "next/link";
import { useEffect, useMemo, useState } from "react";

import type { Business, BusinessType } from "@commerce/types";
import { ApiError } from "@commerce/api-client";
import {
  BusinessCard,
  CategoryChip,
  EmptyState,
  SearchBar,
  Skeleton,
} from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

const CATEGORIES: { label: string; type?: BusinessType }[] = [
  { label: "All" },
  { label: "Food", type: "FOOD" },
  { label: "Grocery", type: "GROCERY" },
  { label: "Retail", type: "RETAIL" },
  { label: "Courier", type: "COURIER" },
];

export default function HomePage() {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<BusinessType | "ALL">("ALL");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        if (!session.getAccessToken()) {
          setBusinesses([]);
          return;
        }
        const list = await getApiClient().listBusinesses({ status: "ACTIVE" });
        setBusinesses(list);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Could not load stores");
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return businesses.filter((b) => {
      if (category !== "ALL" && b.type !== category) return false;
      if (!q) return true;
      return (
        b.name.toLowerCase().includes(q) ||
        (b.description?.toLowerCase().includes(q) ?? false)
      );
    });
  }, [businesses, search, category]);

  if (!session.getAccessToken()) {
    return (
      <div className="space-y-6">
        <div className="rounded-2xl bg-white p-6 shadow-sm">
          <h1 className="text-2xl font-bold text-gray-900">Food, grocery & more</h1>
          <p className="mt-2 text-sm text-gray-500">
            Order from local stores — same engines as Swiggy / Instamart, wired to your tenant API.
          </p>
          <Link
            href="/login"
            className="mt-4 inline-block rounded-xl bg-[var(--brand)] px-6 py-3 text-sm font-semibold text-white"
          >
            Sign in to order
          </Link>
        </div>
        <EmptyState
          title="Set up in Settings"
          description="Add tenant ID, register, then browse restaurants and stores near you."
          action={
            <Link href="/settings" className="text-sm font-medium text-[var(--brand)] underline">
              Open settings
            </Link>
          }
        />
      </div>
    );
  }

  return (
    <div className="space-y-5">
      <SearchBar value={search} onChange={setSearch} placeholder="Search for dishes & stores" />

      <div className="flex gap-2 overflow-x-auto pb-1 scrollbar-hide">
        {CATEGORIES.map((c) => (
          <CategoryChip
            key={c.label}
            label={c.label}
            active={c.type === undefined ? category === "ALL" : category === c.type}
            onClick={() => setCategory(c.type ?? "ALL")}
          />
        ))}
      </div>

      <div>
        <h2 className="text-lg font-bold text-gray-900">Deliver to you</h2>
        <p className="text-sm text-gray-500">Popular in your tenant</p>
      </div>

      {loading ? (
        <div className="grid gap-4 sm:grid-cols-2">
          <Skeleton className="h-48" />
          <Skeleton className="h-48" />
        </div>
      ) : null}

      {error ? <p className="text-sm text-red-600">{error}</p> : null}

      {!loading && filtered.length === 0 ? (
        <EmptyState title="No stores found" description="Try another category or search term." />
      ) : null}

      <div className="grid gap-4 sm:grid-cols-2">
        {filtered.map((business) => (
          <Link key={business.id} href={`/business/${business.id}`} className="block">
            <BusinessCard
              name={business.name}
              type={business.type}
              description={business.description}
            />
          </Link>
        ))}
      </div>
    </div>
  );
}
