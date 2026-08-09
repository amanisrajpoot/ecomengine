"use client";

import { ApiError } from "@commerce/api-client";
import type { Addon, Business } from "@commerce/types";
import { AddonCard, Button, EmptyState, Spinner, TextField, useToast } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useMemo, useState } from "react";

import { businessHasCatalog, rupeesToPaise } from "../../../lib/catalog-helpers";
import { api, getBusinessId, getToken, setBusinessId } from "../../../lib/session";

export default function CatalogAddonsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [businesses, setBusinesses] = useState<Business[]>([]);
  const [selectedBusiness, setSelectedBusiness] = useState<string | null>(getBusinessId());
  const [addons, setAddons] = useState<Addon[]>([]);
  const [name, setName] = useState("");
  const [priceRupees, setPriceRupees] = useState("29.00");
  const [maxQty, setMaxQty] = useState("1");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const catalogBusinesses = useMemo(
    () => businesses.filter((b) => businessHasCatalog(b.capabilities)),
    [businesses],
  );

  const loadAddons = useCallback(async (businessId: string) => {
    const rows = await api().listAddons(businessId);
    setAddons(rows);
  }, []);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const biz = await api().listBusinesses({ status: "ACTIVE" });
        if (cancelled) return;
        setBusinesses(biz);
        const capable = biz.filter((b) => businessHasCatalog(b.capabilities));
        const current =
          selectedBusiness && capable.some((b) => b.id === selectedBusiness)
            ? selectedBusiness
            : capable[0]?.id ?? null;
        if (current && current !== selectedBusiness) {
          setSelectedBusiness(current);
          setBusinessId(current);
        }
        if (current) await loadAddons(current);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load addons");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [loadAddons, router, selectedBusiness]);

  async function onBusinessChange(id: string) {
    setSelectedBusiness(id);
    setBusinessId(id);
    setLoading(true);
    setError(null);
    try {
      await loadAddons(id);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to load addons");
    } finally {
      setLoading(false);
    }
  }

  async function onCreate(event: React.FormEvent) {
    event.preventDefault();
    if (!selectedBusiness || !name.trim()) return;
    setBusy(true);
    setError(null);
    try {
      const row = await api().createAddon(selectedBusiness, {
        name: name.trim(),
        price_paise: rupeesToPaise(priceRupees),
        max_qty: Math.max(1, Number.parseInt(maxQty, 10) || 1),
        is_active: true,
      });
      setAddons((rows) => [...rows, row]);
      setName("");
      toast({ title: "Addon created", variant: "success" });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create addon");
    } finally {
      setBusy(false);
    }
  }

  async function toggleActive(addon: Addon) {
    if (!selectedBusiness) return;
    try {
      const updated = await api().updateAddon(selectedBusiness, addon.id, {
        is_active: !addon.is_active,
      });
      setAddons((rows) => rows.map((row) => (row.id === addon.id ? updated : row)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update addon");
    }
  }

  return (
    <main className="mx-auto max-w-3xl px-5 py-10">
      <Link href="/catalog" className="text-sm text-amber-100/50 hover:text-amber-50">
        ← Catalog
      </Link>
      <p className="mt-4 font-display text-4xl text-amber-50">Addons</p>
      <p className="mt-2 text-sm text-amber-100/55">
        Extras like cheese, toppings, or gift wrap — link them to products from the product page.
      </p>

      {catalogBusinesses.length === 0 && !loading ? (
        <EmptyState
          className="mt-8 border-amber-200/15"
          title="Catalog not enabled"
          description="Addons are only available for catalog-enabled businesses."
        />
      ) : (
        <label className="mt-6 flex max-w-md flex-col gap-1.5 text-sm text-amber-50/80">
          <span>Business</span>
          <select
            className="rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
            value={selectedBusiness ?? ""}
            onChange={(e) => void onBusinessChange(e.target.value)}
          >
            {catalogBusinesses.map((b) => (
              <option key={b.id} value={b.id}>
                {b.name} ({b.type})
              </option>
            ))}
          </select>
        </label>
      )}

      {loading ? (
        <div className="mt-12 flex justify-center">
          <Spinner size="lg" className="text-amber-300" />
        </div>
      ) : null}
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}

      {!loading && catalogBusinesses.length > 0 ? (
        <>
          <form
            className="mt-8 flex flex-col gap-3 rounded-2xl border border-amber-200/10 bg-amber-950/15 p-4"
            onSubmit={onCreate}
          >
            <p className="text-sm font-medium text-amber-50/80">New addon</p>
            <TextField
              label="Name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
            />
            <div className="grid gap-3 sm:grid-cols-2">
              <TextField
                label="Price (₹)"
                type="number"
                min="0"
                step="0.01"
                value={priceRupees}
                onChange={(e) => setPriceRupees(e.target.value)}
                className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
              />
              <TextField
                label="Max quantity"
                type="number"
                min="1"
                value={maxQty}
                onChange={(e) => setMaxQty(e.target.value)}
                className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
              />
            </div>
            <Button type="submit" variant="soft" disabled={busy}>
              {busy ? "Creating…" : "Create addon"}
            </Button>
          </form>

          <ul className="mt-8 flex flex-col gap-2">
            {addons.map((addon) => (
              <li key={addon.id}>
                <AddonCard
                  addon={addon}
                  className="!border-amber-200/10 !bg-amber-950/20"
                  actions={
                    <Button
                      type="button"
                      variant="ghost"
                      className="!px-2 !py-1 !text-xs"
                      onClick={() => void toggleActive(addon)}
                    >
                      {addon.is_active ? "Deactivate" : "Activate"}
                    </Button>
                  }
                />
              </li>
            ))}
          </ul>
        </>
      ) : null}

      {!loading && !error && catalogBusinesses.length > 0 && addons.length === 0 ? (
        <EmptyState
          className="mt-8 border-amber-200/15"
          title="No addons yet"
          description="Create extras for food toppings, sides, or packaging options."
        />
      ) : null}
    </main>
  );
}
