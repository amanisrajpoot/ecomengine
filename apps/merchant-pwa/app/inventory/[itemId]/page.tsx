"use client";

import { ApiError } from "@commerce/api-client";
import type { InventoryItem, StockMovement } from "@commerce/types";
import { Button, Spinner, TextField } from "@commerce/ui";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";

import { loadVariantLabels, variantDisplay, type VariantLabel } from "../../../lib/inventory-helpers";
import { api, getBusinessId, getToken } from "../../../lib/session";

export default function InventoryDetailPage() {
  const router = useRouter();
  const params = useParams<{ itemId: string }>();
  const [item, setItem] = useState<InventoryItem | null>(null);
  const [movements, setMovements] = useState<StockMovement[]>([]);
  const [label, setLabel] = useState<VariantLabel | undefined>();
  const [receiveQty, setReceiveQty] = useState("10");
  const [adjustQty, setAdjustQty] = useState("0");
  const [note, setNote] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);

  const businessId = getBusinessId();

  const load = useCallback(async () => {
    if (!businessId) return;
    const data = await api().getInventoryItem(businessId, params.itemId);
    setItem(data);
    const labels = await loadVariantLabels(api(), businessId);
    setLabel(labels.get(data.variant_id));
    const rows = await api().listInventoryMovements(businessId, params.itemId);
    setMovements(rows);
    return data;
  }, [businessId, params.itemId]);

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");
      return;
    }
    if (!businessId) {
      router.replace("/inventory");
      return;
    }
    let cancelled = false;
    (async () => {
      try {
        await load();
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof ApiError ? err.message : "Stock item not found");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [businessId, load, router]);

  async function receiveStock() {
    if (!businessId || !item) return;
    const delta = Number(receiveQty);
    if (!Number.isFinite(delta) || delta <= 0) {
      setError("Enter a positive quantity to receive.");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const updated = await api().adjustInventory(businessId, item.id, {
        delta_on_hand: delta,
        reason: "RECEIVE",
        note: note || "Received via merchant PWA",
      });
      setItem(updated);
      const rows = await api().listInventoryMovements(businessId, item.id);
      setMovements(rows);
      setNote("");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Receive failed");
    } finally {
      setBusy(false);
    }
  }

  async function adjustStock() {
    if (!businessId || !item) return;
    const delta = Number(adjustQty);
    if (!Number.isFinite(delta) || delta === 0) {
      setError("Enter a non-zero adjustment (+ or −).");
      return;
    }
    setBusy(true);
    setError(null);
    try {
      const updated = await api().adjustInventory(businessId, item.id, {
        delta_on_hand: delta,
        reason: "ADJUSTMENT",
        note: note || "Adjusted via merchant PWA",
      });
      setItem(updated);
      const rows = await api().listInventoryMovements(businessId, item.id);
      setMovements(rows);
      setNote("");
      setAdjustQty("0");
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Adjustment failed");
    } finally {
      setBusy(false);
    }
  }

  if (loading) {
    return (
      <main className="mx-auto flex max-w-xl justify-center px-5 py-20">
        <Spinner size="lg" className="text-amber-300" />
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-xl px-5 py-10">
      <Link href="/inventory" className="text-sm text-amber-100/50 hover:text-amber-50">
        ← Stock board
      </Link>
      <p className="mt-4 font-display text-4xl text-amber-50">Stock item</p>
      {error ? <p className="mt-4 text-rose-300">{error}</p> : null}
      {item ? (
        <div className="mt-8 space-y-6">
          <section className="rounded-2xl border border-amber-200/10 bg-amber-950/25 px-4 py-4">
            <p className="text-lg font-medium text-amber-50">
              {variantDisplay(label, item.variant_id)}
            </p>
            {label?.sku ? (
              <p className="mt-1 text-xs text-amber-100/45">SKU {label.sku}</p>
            ) : null}
            <div className="mt-4 grid grid-cols-3 gap-3 text-center text-sm">
              <div>
                <p className="text-2xl font-semibold text-amber-50">{item.available}</p>
                <p className="text-xs text-amber-100/45">Available</p>
              </div>
              <div>
                <p className="text-2xl font-semibold text-amber-50">{item.on_hand}</p>
                <p className="text-xs text-amber-100/45">On hand</p>
              </div>
              <div>
                <p className="text-2xl font-semibold text-amber-50">{item.reserved}</p>
                <p className="text-xs text-amber-100/45">Reserved</p>
              </div>
            </div>
            {item.low_stock_threshold != null ? (
              <p className="mt-3 text-xs text-amber-100/45">
                Low-stock threshold: {item.low_stock_threshold}
              </p>
            ) : null}
          </section>

          <section className="rounded-2xl border border-amber-200/10 px-4 py-4">
            <p className="text-sm font-medium text-amber-50/90">Receive stock</p>
            <div className="mt-3 flex flex-col gap-3">
              <TextField
                label="Quantity to receive"
                type="number"
                min="1"
                value={receiveQty}
                onChange={(e) => setReceiveQty(e.target.value)}
              />
              <TextField
                label="Note (optional)"
                value={note}
                onChange={(e) => setNote(e.target.value)}
              />
              <Button disabled={busy} onClick={() => void receiveStock()}>
                {busy ? "Saving…" : "Receive"}
              </Button>
            </div>
          </section>

          <section className="rounded-2xl border border-amber-200/10 px-4 py-4">
            <p className="text-sm font-medium text-amber-50/90">Adjust stock</p>
            <p className="mt-1 text-xs text-amber-100/45">
              Use negative numbers for shrinkage or corrections.
            </p>
            <div className="mt-3 flex flex-col gap-3">
              <TextField
                label="Adjustment (+/−)"
                type="number"
                value={adjustQty}
                onChange={(e) => setAdjustQty(e.target.value)}
              />
              <Button variant="soft" disabled={busy} onClick={() => void adjustStock()}>
                {busy ? "Saving…" : "Apply adjustment"}
              </Button>
            </div>
          </section>

          <section>
            <p className="text-sm font-medium text-amber-50/90">Movement history</p>
            <ul className="mt-3 divide-y divide-amber-200/10 rounded-2xl border border-amber-200/10">
              {movements.length === 0 ? (
                <li className="px-4 py-3 text-sm text-amber-100/45">No movements yet.</li>
              ) : (
                movements.map((movement) => (
                  <li key={movement.id} className="px-4 py-3 text-sm">
                    <div className="flex items-center justify-between gap-3">
                      <span className="font-medium text-amber-50">{movement.reason}</span>
                      <span className="text-amber-100/60">
                        {new Date(movement.created_at).toLocaleString("en-IN")}
                      </span>
                    </div>
                    <p className="mt-1 text-amber-100/55">
                      on_hand {movement.delta_on_hand >= 0 ? "+" : ""}
                      {movement.delta_on_hand}
                      {movement.delta_reserved
                        ? ` · reserved ${movement.delta_reserved >= 0 ? "+" : ""}${movement.delta_reserved}`
                        : ""}
                    </p>
                    {movement.note ? (
                      <p className="mt-1 text-xs text-amber-100/40">{movement.note}</p>
                    ) : null}
                  </li>
                ))
              )}
            </ul>
          </section>
        </div>
      ) : null}
    </main>
  );
}
