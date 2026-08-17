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
    <div className="space-y-5">
      <Link
        href={`/business/${businessId}/catalog`}
        className="text-sm font-medium text-[var(--brand)]"
      >
        ← Back to menu
      </Link>
      <h1 className="text-2xl font-bold text-gray-900">New menu item</h1>
      <Card variant="light">
        <form className="space-y-3" onSubmit={onSubmit}>
          <Input
            variant="light"
            label="Name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <Input
            variant="light"
            label="Description"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <Button type="submit" variant="brand" disabled={loading || !name.trim()}>
            {loading ? "Creating…" : "Create item"}
          </Button>
        </form>
      </Card>
      {error ? <p className="text-sm text-red-600">{error}</p> : null}
    </div>
  );
}
