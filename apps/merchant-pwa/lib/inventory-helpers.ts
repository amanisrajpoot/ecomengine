import type { ApiClient } from "@commerce/api-client";

export type VariantLabel = {
  variantId: string;
  productName: string;
  variantName: string;
  sku: string | null;
};

export async function loadVariantLabels(
  client: ApiClient,
  businessId: string,
): Promise<Map<string, VariantLabel>> {
  const map = new Map<string, VariantLabel>();
  const products = await client.listProducts(businessId);
  await Promise.all(
    products.map(async (product) => {
      const variants = await client.listVariants(businessId, product.id);
      for (const variant of variants) {
        map.set(variant.id, {
          variantId: variant.id,
          productName: product.name,
          variantName: variant.name,
          sku: variant.sku,
        });
      }
    }),
  );
  return map;
}

export function variantDisplay(label: VariantLabel | undefined, variantId: string): string {
  if (!label) return variantId.slice(0, 8);
  return `${label.productName} · ${label.variantName}`;
}

export function businessHasInventory(capabilities: Record<string, unknown> | undefined): boolean {
  return Boolean(capabilities?.inventory);
}
