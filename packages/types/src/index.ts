/** Shared domain primitives. */

export type TenantId = string;
export type UserId = string;

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: UserId;
  tenant_id: TenantId | null;
}

export interface RoleBinding {
  id: string;
  user_id: UserId;
  role: string;
  tenant_id: TenantId | null;
  business_id: string | null;
  created_at: string;
}

export interface User {
  id: UserId;
  tenant_id: TenantId | null;
  email: string | null;
  phone: string | null;
  status: string;
  display_name: string | null;
  created_at: string;
  updated_at: string;
  roles: RoleBinding[];
}

export interface Tenant {
  id: TenantId;
  name: string;
  slug: string;
  status: string;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export type BusinessType = "FOOD" | "RETAIL" | "GROCERY" | "COURIER";
export type BusinessStatus = "DRAFT" | "ACTIVE" | "PAUSED";

export interface BusinessContact {
  phone?: string | null;
  email?: string | null;
  whatsapp?: string | null;
}

export interface BusinessConfig {
  preparation_time_minutes?: number | null;
  accepts_scheduled_orders?: boolean;
  currency?: string;
  timezone?: string;
  extra?: Record<string, unknown>;
}

export interface BusinessCapabilities {
  catalog: boolean;
  inventory: boolean;
  addons: boolean;
  delivery: boolean;
  scheduledOrders: boolean;
}

export interface Business {
  id: string;
  tenant_id: TenantId;
  type: BusinessType;
  name: string;
  description: string | null;
  logo_url: string | null;
  contact: BusinessContact;
  settings: BusinessConfig;
  capabilities: BusinessCapabilities;
  status: BusinessStatus;
  created_at: string;
  updated_at: string;
}

export interface Address {
  line1: string;
  line2?: string | null;
  landmark?: string | null;
  city: string;
  state: string;
  pincode: string;
  country?: string;
}

export interface DayHours {
  day: "MON" | "TUE" | "WED" | "THU" | "FRI" | "SAT" | "SUN";
  open?: string | null;
  close?: string | null;
  closed?: boolean;
}

export interface BusinessLocation {
  id: string;
  tenant_id: TenantId;
  business_id: string;
  name: string;
  address: Address;
  lat: number;
  lng: number;
  service_area: Record<string, unknown> | null;
  hours: DayHours[];
  timezone: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: string;
  tenant_id: TenantId;
  business_id: string;
  parent_id: string | null;
  name: string;
  sort_order: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Product {
  id: string;
  tenant_id: TenantId;
  business_id: string;
  category_id: string | null;
  name: string;
  description: string | null;
  images: string[];
  tags: string[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Variant {
  id: string;
  tenant_id: TenantId;
  product_id: string;
  name: string;
  sku: string | null;
  base_price_paise: number;
  is_available: boolean;
  meta: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface Addon {
  id: string;
  tenant_id: TenantId;
  business_id: string;
  name: string;
  price_paise: number;
  max_qty: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductAddonLink {
  product_id: string;
  addon_id: string;
  group_name: string | null;
  is_required: boolean;
}

export interface BundleItem {
  variant_id: string;
  quantity: number;
}

export interface Bundle {
  id: string;
  tenant_id: TenantId;
  business_id: string;
  name: string;
  price_paise: number | null;
  items: BundleItem[];
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface InventoryItem {
  id: string;
  tenant_id: TenantId;
  business_id: string;
  location_id: string;
  variant_id: string;
  on_hand: number;
  reserved: number;
  low_stock_threshold: number | null;
  available: number;
  updated_at: string;
}

export interface StockMovement {
  id: string;
  tenant_id: TenantId;
  inventory_item_id: string;
  reason: string;
  delta_on_hand: number;
  delta_reserved: number;
  reference_type: string | null;
  reference_id: string | null;
  created_by: string | null;
  created_at: string;
}

export interface TaxLine {
  code: string;
  rate_bps: number;
  amount_paise: number;
}

export interface PriceLine {
  cart_item_id?: string | null;
  variant_id?: string | null;
  bundle_id?: string | null;
  name: string;
  quantity: number;
  unit_price_paise: number;
  line_total_paise: number;
  addons?: Record<string, unknown>[];
}

export interface PriceBreakdown {
  currency: string;
  subtotal_paise: number;
  discount_paise: number;
  delivery_fee_paise: number;
  platform_fee_paise: number;
  other_fees_paise: number;
  tax_paise: number;
  tax_lines: TaxLine[];
  total_paise: number;
  lines: PriceLine[];
}

export interface CartItem {
  id: string;
  cart_id: string;
  variant_id: string | null;
  bundle_id: string | null;
  quantity: number;
  addons: Record<string, unknown>[];
  unit_price_paise: number;
  meta: Record<string, unknown>;
}

export interface Cart {
  id: string;
  tenant_id: TenantId;
  customer_id: UserId;
  business_id: string | null;
  location_id: string | null;
  currency: string;
  pricing_snapshot: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  items?: CartItem[];
}

export interface CartWithPricing extends Cart {
  pricing?: PriceBreakdown | null;
}

export interface TaxRule {
  id: string;
  tenant_id: TenantId | null;
  code: string;
  category: string;
  jurisdiction: string;
  rate_bps: number;
  inclusive: boolean;
  payer: string;
  kind: string;
  effective_from: string;
  effective_to: string | null;
  created_at: string;
  updated_at: string;
}

export interface TaxCalculationLine {
  code: string;
  kind: string;
  category: string;
  rate_bps: number;
  taxable_paise: number;
  amount_paise: number;
  payer: string;
}

export interface TaxCalculationResult {
  tax_paise: number;
  lines: TaxCalculationLine[];
}
