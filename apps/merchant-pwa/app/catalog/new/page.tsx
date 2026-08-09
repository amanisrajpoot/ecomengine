"use client";

import { ApiError } from "@commerce/api-client";
import type { Category } from "@commerce/types";
import { Button, Spinner, TextField, useToast } from "@commerce/ui";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

import { businessHasCatalog, paiseToRupeesInput, rupeesToPaise } from "../../../lib/catalog-helpers";
import { api, getBusinessId, getToken } from "../../../lib/session";

export default function NewCatalogProductPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [businessId, setBusinessId] = useState<string | null>(getBusinessId());
  const [categories, setCategories] = useState<Category[]>([]);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [newCategoryName, setNewCategoryName] = useState("");
  const [variantName, setVariantName] = useState("Regular");
  const [sku, setSku] = useState("");
  const [priceRupees, setPriceRupees] = useState("99.00");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        const biz = await api().listBusinesses({ status: "ACTIVE" });
        const capable = biz.filter((b) => businessHasCatalog(b.capabilities));
        const current =
          businessId && capable.some((b) => b.id === businessId)
            ? businessId
            : capable[0]?.id ?? null;
        if (!current) {
          setError("No catalog-enabled business found.");
          setLoading(false);
          return;
        }
        setBusinessId(current);
        const cats = await api().listCategories(current);
        if (!cancelled) {
          setCategories(cats);
          setCategoryId(cats[0]?.id ?? "");
        }
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load categories");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [businessId, router]);

  async function onSubmit(event: React.FormEvent) {
    event.preventDefault();
    if (!businessId || !name.trim()) {
      setError("Product name is required.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      let resolvedCategoryId = categoryId || null;
      if (newCategoryName.trim()) {
        const cat = await api().createCategory(businessId, { name: newCategoryName.trim() });
        resolvedCategoryId = cat.id;
      }
      const product = await api().createProduct(businessId, {
        name: name.trim(),
        description: description.trim() || null,
        category_id: resolvedCategoryId,
        is_active: true,
      });
      await api().createVariant(businessId, product.id, {
        name: variantName.trim() || "Regular",
        sku: sku.trim() || null,
        base_price_paise: rupeesToPaise(priceRupees),
        is_available: true,
      });
      toast({ title: "Product created", variant: "success" });
      router.push(`/catalog/${product.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to create product");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto max-w-lg px-5 py-16">
        <Spinner size="lg" className="text-amber-300" />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-lg px-5 py-10">
      <Link href="/catalog" className="text-sm text-amber-100/50 hover:text-amber-50">
        ← Catalog
      </Link>
      <p className="mt-4 font-display text-4xl text-amber-50">New product</p>

      <form className="mt-8 flex flex-col gap-4" onSubmit={onSubmit}>
        <TextField
          label="Product name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          required
          className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
        />
        <label className="flex flex-col gap-1.5 text-sm text-amber-50/80">
          <span>Description (optional)</span>
          <textarea
            className="min-h-24 rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
        </label>
        <label className="flex flex-col gap-1.5 text-sm text-amber-50/80">
          <span>Category</span>
          <select
            className="rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
            value={categoryId}
            onChange={(e) => setCategoryId(e.target.value)}
          >
            <option value="">Uncategorized</option>
            {categories.map((cat) => (
              <option key={cat.id} value={cat.id}>
                {cat.name}
              </option>
            ))}
          </select>
        </label>
        <TextField
          label="Or new category name"
          value={newCategoryName}
          onChange={(e) => setNewCategoryName(e.target.value)}
          placeholder="e.g. Mains"
          className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
        />

        <p className="mt-2 text-sm font-medium text-amber-100/70">First variant</p>
        <TextField
          label="Variant name"
          value={variantName}
          onChange={(e) => setVariantName(e.target.value)}
          className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
        />
        <TextField
          label="SKU (optional)"
          value={sku}
          onChange={(e) => setSku(e.target.value)}
          className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
        />
        <TextField
          label="Price (₹)"
          type="number"
          min="0"
          step="0.01"
          value={priceRupees}
          onChange={(e) => setPriceRupees(e.target.value)}
          className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
        />

        {error ? <p className="text-rose-300">{error}</p> : null}

        <div className="mt-2 flex gap-3">
          <Button type="submit" disabled={busy}>
            {busy ? "Saving…" : "Create product"}
          </Button>
          <Link href="/catalog">
            <Button type="button" variant="ghost">
              Cancel
            </Button>
          </Link>
        </div>
      </form>
      <p className="mt-4 text-xs text-amber-100/40">
        Default price preview: ₹{paiseToRupeesInput(rupeesToPaise(priceRupees))}
      </p>
    </main>
  );
}
