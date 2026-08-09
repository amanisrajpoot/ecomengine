"use client";

import { ApiError } from "@commerce/api-client";
import type { Addon, Category, Product, ProductAddonLink, Variant } from "@commerce/types";
import { AddonCard, Button, formatPaise, Spinner, TextField, useToast, VariantRow } from "@commerce/ui";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { paiseToRupeesInput, rupeesToPaise } from "../../../lib/catalog-helpers";
import { api, getBusinessId, getToken } from "../../../lib/session";

export default function CatalogProductPage() {
  const router = useRouter();
  const params = useParams<{ productId: string }>();
  const { toast } = useToast();
  const [businessId, setBusinessId] = useState<string | null>(getBusinessId());
  const [product, setProduct] = useState<Product | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [variants, setVariants] = useState<Variant[]>([]);
  const [allAddons, setAllAddons] = useState<Addon[]>([]);
  const [linkedAddons, setLinkedAddons] = useState<ProductAddonLink[]>([]);
  const [linkAddonId, setLinkAddonId] = useState("");
  const [linkGroupName, setLinkGroupName] = useState("");
  const [linkRequired, setLinkRequired] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [categoryId, setCategoryId] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [newVariantName, setNewVariantName] = useState("");
  const [newVariantSku, setNewVariantSku] = useState("");
  const [newVariantPrice, setNewVariantPrice] = useState("0.00");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [addingVariant, setAddingVariant] = useState(false);
  const [linkingAddon, setLinkingAddon] = useState(false);

  const load = useCallback(async () => {
    const bid = getBusinessId();
    if (!bid) throw new Error("Select a business first");
    setBusinessId(bid);
    const [prod, cats, vars, addons, links] = await Promise.all([
      api().getProduct(bid, params.productId),
      api().listCategories(bid),
      api().listVariants(bid, params.productId),
      api().listAddons(bid),
      api().listProductAddons(bid, params.productId),
    ]);
    setProduct(prod);
    setCategories(cats);
    setVariants(vars);
    setAllAddons(addons.filter((row) => row.is_active));
    setLinkedAddons(links);
    setName(prod.name);
    setDescription(prod.description ?? "");
    setCategoryId(prod.category_id ?? "");
    setIsActive(prod.is_active);
  }, [params.productId]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        await load();
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Failed to load product");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [load, router]);

  async function onSaveProduct(event: React.FormEvent) {
    event.preventDefault();
    if (!businessId) return;
    setSaving(true);
    setError(null);
    try {
      const updated = await api().updateProduct(businessId, params.productId, {
        name: name.trim(),
        description: description.trim() || null,
        category_id: categoryId || null,
        is_active: isActive,
      });
      setProduct(updated);
      toast({ title: "Product updated", variant: "success" });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to save product");
    } finally {
      setSaving(false);
    }
  }

  async function onAddVariant(event: React.FormEvent) {
    event.preventDefault();
    if (!businessId || !newVariantName.trim()) return;
    setAddingVariant(true);
    setError(null);
    try {
      const row = await api().createVariant(businessId, params.productId, {
        name: newVariantName.trim(),
        sku: newVariantSku.trim() || null,
        base_price_paise: rupeesToPaise(newVariantPrice),
        is_available: true,
      });
      setVariants((rows) => [...rows, row]);
      setNewVariantName("");
      setNewVariantSku("");
      setNewVariantPrice("0.00");
      toast({ title: "Variant added", variant: "success" });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to add variant");
    } finally {
      setAddingVariant(false);
    }
  }

  async function toggleVariantAvailability(variant: Variant) {
    if (!businessId) return;
    try {
      const updated = await api().updateVariant(businessId, params.productId, variant.id, {
        is_available: !variant.is_available,
      });
      setVariants((rows) => rows.map((row) => (row.id === variant.id ? updated : row)));
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to update variant");
    }
  }

  const addonMap = new Map(allAddons.map((row) => [row.id, row]));
  const linkedAddonIds = new Set(linkedAddons.map((row) => row.addon_id));
  const availableToLink = allAddons.filter((row) => !linkedAddonIds.has(row.id));

  async function onLinkAddon(event: React.FormEvent) {
    event.preventDefault();
    if (!businessId || !linkAddonId) return;
    setLinkingAddon(true);
    setError(null);
    try {
      const link = await api().linkProductAddon(businessId, params.productId, {
        addon_id: linkAddonId,
        group_name: linkGroupName.trim() || null,
        is_required: linkRequired,
      });
      setLinkedAddons((rows) => [...rows, link]);
      setLinkAddonId(availableToLink[0]?.id ?? "");
      setLinkGroupName("");
      setLinkRequired(false);
      toast({ title: "Addon linked", variant: "success" });
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Failed to link addon");
    } finally {
      setLinkingAddon(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto max-w-lg px-5 py-16">
        <Spinner size="lg" className="text-amber-300" />
      </main>
    );
  }

  if (!product) {
    return (
      <main className="mx-auto max-w-lg px-5 py-10">
        <p className="text-rose-300">{error ?? "Product not found"}</p>
        <Link href="/catalog" className="mt-4 inline-block text-amber-100/60 hover:text-amber-50">
          ← Back to catalog
        </Link>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-lg px-5 py-10">
      <Link href="/catalog" className="text-sm text-amber-100/50 hover:text-amber-50">
        ← Catalog
      </Link>
      <p className="mt-4 font-display text-4xl text-amber-50">{product.name}</p>

      <form className="mt-8 flex flex-col gap-4" onSubmit={onSaveProduct}>
        <TextField
          label="Product name"
          value={name}
          onChange={(e) => setName(e.target.value)}
          className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
        />
        <label className="flex flex-col gap-1.5 text-sm text-amber-50/80">
          <span>Description</span>
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
        <label className="flex items-center gap-2 text-sm text-amber-100/70">
          <input
            type="checkbox"
            checked={isActive}
            onChange={(e) => setIsActive(e.target.checked)}
            className="rounded border-amber-200/20"
          />
          Product is active (visible to customers)
        </label>
        <Button type="submit" disabled={saving}>
          {saving ? "Saving…" : "Save product"}
        </Button>
      </form>

      <section className="mt-10">
        <h2 className="text-sm uppercase tracking-wide text-amber-200/50">Variants</h2>
        <ul className="mt-3 flex flex-col gap-2">
          {variants.map((variant) => (
            <li key={variant.id}>
              <VariantRow
                variant={variant}
                className="!border-amber-200/10 !bg-amber-950/20"
                actions={
                  <Button
                    type="button"
                    variant="ghost"
                    className="!px-2 !py-1 !text-xs"
                    onClick={() => void toggleVariantAvailability(variant)}
                  >
                    {variant.is_available ? "Mark unavailable" : "Mark available"}
                  </Button>
                }
              />
            </li>
          ))}
        </ul>

        <form className="mt-6 flex flex-col gap-3 rounded-2xl border border-amber-200/10 bg-amber-950/15 p-4" onSubmit={onAddVariant}>
          <p className="text-sm font-medium text-amber-50/80">Add variant</p>
          <TextField
            label="Name"
            value={newVariantName}
            onChange={(e) => setNewVariantName(e.target.value)}
            className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
          />
          <TextField
            label="SKU"
            value={newVariantSku}
            onChange={(e) => setNewVariantSku(e.target.value)}
            className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
          />
          <TextField
            label="Price (₹)"
            type="number"
            min="0"
            step="0.01"
            value={newVariantPrice}
            onChange={(e) => setNewVariantPrice(e.target.value)}
            className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
          />
          <Button type="submit" variant="soft" disabled={addingVariant}>
            {addingVariant ? "Adding…" : "Add variant"}
          </Button>
        </form>
      </section>

      <section className="mt-10">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-sm uppercase tracking-wide text-amber-200/50">Linked addons</h2>
          <Link href="/catalog/addons" className="text-xs text-amber-100/50 hover:text-amber-50">
            Manage addons →
          </Link>
        </div>
        <ul className="mt-3 flex flex-col gap-2">
          {linkedAddons.map((link) => {
            const addon = addonMap.get(link.addon_id);
            if (!addon) return null;
            return (
              <li key={link.id}>
                <AddonCard
                  addon={addon}
                  className="!border-amber-200/10 !bg-amber-950/20"
                />
                <p className="mt-1 px-1 text-xs text-amber-100/45">
                  {link.group_name ? `Group: ${link.group_name} · ` : ""}
                  {link.is_required ? "Required" : "Optional"}
                </p>
              </li>
            );
          })}
        </ul>
        {linkedAddons.length === 0 ? (
          <p className="mt-3 text-sm text-amber-100/45">No addons linked yet.</p>
        ) : null}

        {availableToLink.length > 0 ? (
          <form
            className="mt-6 flex flex-col gap-3 rounded-2xl border border-amber-200/10 bg-amber-950/15 p-4"
            onSubmit={onLinkAddon}
          >
            <p className="text-sm font-medium text-amber-50/80">Link addon</p>
            <label className="flex flex-col gap-1.5 text-sm text-amber-50/80">
              <span>Addon</span>
              <select
                className="rounded-xl border border-amber-200/15 bg-amber-950/40 px-3 py-2.5 text-amber-50"
                value={linkAddonId || availableToLink[0]?.id || ""}
                onChange={(e) => setLinkAddonId(e.target.value)}
              >
                {availableToLink.map((addon) => (
                  <option key={addon.id} value={addon.id}>
                    {addon.name} ({formatPaise(addon.price_paise)})
                  </option>
                ))}
              </select>
            </label>
            <TextField
              label="Group name (optional)"
              value={linkGroupName}
              onChange={(e) => setLinkGroupName(e.target.value)}
              placeholder="e.g. Toppings"
              className="!border-amber-200/15 !bg-amber-950/40 !text-amber-50"
            />
            <label className="flex items-center gap-2 text-sm text-amber-100/70">
              <input
                type="checkbox"
                checked={linkRequired}
                onChange={(e) => setLinkRequired(e.target.checked)}
                className="rounded border-amber-200/20"
              />
              Required selection
            </label>
            <Button type="submit" variant="soft" disabled={linkingAddon}>
              {linkingAddon ? "Linking…" : "Link addon"}
            </Button>
          </form>
        ) : (
          <p className="mt-4 text-sm text-amber-100/45">
            {allAddons.length === 0
              ? "Create addons first from the addons page."
              : "All addons are already linked to this product."}
          </p>
        )}
      </section>

      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
    </main>
  );
}
