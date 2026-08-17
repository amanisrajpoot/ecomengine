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

export default function ExplorePage() {
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState<BusinessType | "ALL">("ALL");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(null);
      try {
        if (!session.getAccessToken()) {
          setError("Sign in to explore.");
          return;
        }
        const list = await getApiClient().listBusinesses({ status: "ACTIVE" });
        setBusinesses(list);
      } catch (err) {
        setError(err instanceof ApiError ? err.message : "Failed to load stores");
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

  return (
    <div className="space-y-5">
      <h1 className="text-xl font-bold text-gray-900">Explore</h1>
      <SearchBar value={search} onChange={setSearch} />
      <div className="flex gap-2 overflow-x-auto pb-1">
        {CATEGORIES.map((c) => (
          <CategoryChip
            key={c.label}
            label={c.label}
            active={c.type === undefined ? category === "ALL" : category === c.type}
            onClick={() => setCategory(c.type ?? "ALL")}
          />
        ))}
      </div>
      {loading ? (
        <div className="space-y-3">
          <Skeleton className="h-40" />
          <Skeleton className="h-40" />
        </div>
      ) : null}
      {error ? (
        <p className="text-sm text-red-600">
          {error} <Link href="/login" className="underline">Sign in</Link>
        </p>
      ) : null}
      {!loading && filtered.length === 0 && !error ? (
        <EmptyState title="No stores match" />
      ) : null}
      <div className="grid gap-4">
        {filtered.map((business) => (
          <Link key={business.id} href={`/business/${business.id}`}>
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
