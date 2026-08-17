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
