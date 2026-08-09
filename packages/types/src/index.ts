/** Shared domain types for Commerce Engine clients. */

export type TenantId = string;
export type UserId = string;
export type BusinessId = string;
export type LocationId = string;
export type OrderId = string;
export type CartId = string;
export type ProductId = string;
export type VariantId = string;

/** Money in integer paise (INR). Never use floating point for currency. */
export type MoneyPaise = number;

export interface Money {
  amountPaise: MoneyPaise;
  currency: "INR";
}

export type BusinessType = "FOOD" | "RETAIL" | "GROCERY" | "COURIER";

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: UserId;
  tenant_id: TenantId | null;
}

export interface NearbyStore {
  business_id: BusinessId;
  business_name: string;
  business_type: BusinessType | string;
  location_id: LocationId;
  location_name: string;
  address: Record<string, unknown>;
  lat: number;
  lng: number;
  distance_km: number;
  service_area?: Record<string, unknown> | null;
  capabilities?: Record<string, unknown>;
}

export interface Product {
  id: ProductId;
  business_id: BusinessId;
  category_id: string | null;
  name: string;
  description: string | null;
  is_active: boolean;
}

export interface Variant {
  id: VariantId;
  product_id: ProductId;
  name: string;
  sku: string | null;
  base_price_paise: MoneyPaise;
  is_available: boolean;
}

export interface Cart {
  id: CartId;
  business_id: BusinessId | null;
  location_id: LocationId | null;
  currency: string;
  pricing_snapshot: Record<string, unknown>;
  status: string;
  items: CartItem[];
}

export interface CartItem {
  id: string;
  variant_id: VariantId | null;
  name_snapshot: string;
  quantity: number;
  unit_price_paise: MoneyPaise;
}

export interface Order {
  id: OrderId;
  status: string;
  state_machine_profile: string;
  fulfillment_type: string;
  payment_method: string;
  pricing_snapshot: Record<string, unknown>;
  metadata: Record<string, unknown>;
  business_id: BusinessId | null;
  created_at: string;
  items: Array<{
    id: string;
    name_snapshot: string;
    quantity: number;
    unit_price_paise: MoneyPaise;
    variant_id: VariantId | null;
  }>;
}

export interface PriceBreakdown {
  currency: string;
  subtotal_paise: MoneyPaise;
  discount_paise: MoneyPaise;
  delivery_fee_paise: MoneyPaise;
  platform_fee_paise: MoneyPaise;
  other_fees_paise: MoneyPaise;
  tax_paise: MoneyPaise;
  total_paise: MoneyPaise;
  lines: Array<{ name: string; quantity: number; unit_price_paise: MoneyPaise }>;
}

export interface CourierQuote {
  distance_km: number;
  weight_kg: number;
  vehicle_type: string;
  express: boolean;
  fare_components: Record<string, number>;
  pricing: PriceBreakdown;
}

export function formatPaise(paise: MoneyPaise): string {
  return new Intl.NumberFormat("en-IN", {
    style: "currency",
    currency: "INR",
    maximumFractionDigits: 2,
  }).format(paise / 100);
}
