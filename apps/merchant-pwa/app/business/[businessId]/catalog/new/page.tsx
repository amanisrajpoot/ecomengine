"use client";

import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { useState } from "react";

import { ApiError } from "@commerce/api-client";
import { Button, Card, Input } from "@commerce/ui";

import { getApiClient } from "@/lib/api";

export default function NewProductPage() {
  const params = useParams<{ businessId: string }>();
  const businessId = params.businessId;
  const router = useRouter();

  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const product = await getApiClient().createProduct(businessId, {
        name,
        description: description || undefined,
      });
      router.push(`/business/${businessId}/catalog/${product.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create product");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <Link
        href={`/business/${businessId}/catalog`}
        className="text-xs text-amber-300/70 hover:text-amber-100"
      >
        ← Catalog
      </Link>
      <h1 className="text-2xl font-semibold">New product</h1>
      <Card>
        <form className="space-y-3" onSubmit={onSubmit}>
          <Input label="Name" value={name} onChange={(e) => setName(e.target.value)} required />
          <Input
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <Button type="submit" disabled={loading || !name.trim()}>
            {loading ? "Creating…" : "Create product"}
          </Button>
        </form>
      </Card>
      {error ? <p className="text-sm text-red-300">{error}</p> : null}
    </div>
  );
}
