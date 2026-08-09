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

export interface Addon {
  id: string;
  business_id: BusinessId;
  name: string;
  price_paise: MoneyPaise;
  max_qty: number;
  is_active: boolean;
}

export interface ProductAddonLink {
  id: string;
  product_id: ProductId;
  addon_id: string;
  group_name: string | null;
  is_required: boolean;
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
  status_events?: Array<{
    from_status: string | null;
    to_status: string;
    actor_role: string | null;
    created_at: string;
  }>;
}

export interface Business {
  id: BusinessId;
  name: string;
  type: BusinessType | string;
  status: string;
  capabilities: Record<string, unknown>;
}

export type StockReason =
  | "RECEIVE"
  | "ADJUSTMENT"
  | "RESERVE"
  | "RELEASE"
  | "CONSUME";

export interface InventoryItem {
  id: string;
  tenant_id: string;
  business_id: BusinessId;
  location_id: LocationId;
  variant_id: VariantId;
  on_hand: number;
  reserved: number;
  low_stock_threshold: number | null;
  updated_at: string;
  available: number;
  is_low_stock: boolean;
  is_out_of_stock: boolean;
}

export interface StockMovement {
  id: string;
  tenant_id: string;
  inventory_item_id: string;
  reason: StockReason | string;
  delta_on_hand: number;
  delta_reserved: number;
  reference_type: string | null;
  reference_id: string | null;
  created_at: string;
  created_by: string | null;
  note: string | null;
}

export interface BusinessLocation {
  id: LocationId;
  business_id: BusinessId;
  name: string;
  address: Record<string, unknown>;
  lat: number;
  lng: number;
  is_active: boolean;
}

export interface Fulfillment {
  id: string;
  order_id: OrderId;
  type: string;
  status: string;
}

export interface DeliveryStop {
  id: string;
  delivery_id: string;
  sequence: number;
  stop_type: "PICKUP" | "DROP" | string;
  address: Record<string, unknown>;
  lat: number | null;
  lng: number | null;
  status: string;
  proof: Record<string, unknown> | null;
}

export interface Delivery {
  id: string;
  fulfillment_id: string;
  partner_id: string | null;
  status: string;
  metadata: Record<string, unknown>;
  stops: DeliveryStop[];
}

export interface Partner {
  id: string;
  user_id: string;
  display_name: string | null;
  status: string;
  is_online: boolean;
  current_lat: number | null;
  current_lng: number | null;
}

export interface Tenant {
  id: string;
  name: string;
  slug: string;
  status: string;
  config: Record<string, unknown>;
}

export interface Payment {
  id: string;
  tenant_id: string;
  order_id: string;
  provider: string;
  provider_ref: string | null;
  status: string;
  amount_paise: number;
  currency: string;
  idempotency_key?: string | null;
  checkout_payload: Record<string, unknown>;
  raw: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface PaymentInitiateResponse {
  payment: Payment;
  order_status: string;
}

export interface Notification {
  id: string;
  tenant_id: string;
  user_id: string | null;
  order_id: string | null;
  event_name: string;
  channel: string;
  recipient: string;
  subject: string | null;
  body: string;
  status: string;
  provider: string | null;
  provider_ref: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface Refund {
  id: string;
  tenant_id: string;
  payment_id: string;
  order_id: string;
  provider_ref: string | null;
  amount_paise: number;
  status: string;
  reason: string | null;
  raw: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Settlement {
  id: string;
  tenant_id: string;
  party_type: "MERCHANT" | "RIDER" | "PLATFORM" | string;
  party_id: string;
  status: string;
  period_start: string;
  period_end: string;
  total_paise: number;
  currency: string;
  report: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  ledger_entry_ids: string[];
}

export interface OrderDebugger {
  order: Order;
  payments: Record<string, unknown>[];
  ledger_entries: Record<string, unknown>[];
  ledger_balances: Record<string, unknown>[];
  fulfillment: Record<string, unknown> | null;
  delivery: Record<string, unknown> | null;
  settlements: Record<string, unknown>[];
  vertical: string;
  chain: string[];
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
