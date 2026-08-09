"use client";

import { createApiClient } from "@commerce/api-client";

const TOKEN_KEY = "ce_customer_token";
const TENANT_KEY = "ce_customer_tenant";
const CART_KEY = "ce_customer_cart";
const PHONE_KEY = "ce_customer_phone";
const ADDRESS_KEY = "ce_customer_address";

export type DeliveryAddress = {
  line1: string;
  city: string;
  state: string;
  pincode: string;
  lat?: number;
  lng?: number;
};

export const DEFAULT_DELIVERY_ADDRESS: DeliveryAddress = {
  line1: "Koramangala 5th Block",
  city: "Bengaluru",
  state: "Karnataka",
  pincode: "560038",
  lat: 12.9352,
  lng: 77.6245,
};

export type SessionCart = {
  cartId: string;
  businessId: string;
  locationId?: string | null;
  itemCount?: number;
};

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getTenantId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TENANT_KEY) || process.env.NEXT_PUBLIC_TENANT_ID || null;
}

export function getDefaultTenantId(): string {
  return process.env.NEXT_PUBLIC_TENANT_ID ?? "";
}

export function getCustomerPhone(): string {
  if (typeof window === "undefined") return "";
  return localStorage.getItem(PHONE_KEY) ?? "9876543210";
}

export function setCustomerPhone(phone: string) {
  localStorage.setItem(PHONE_KEY, phone);
}

export function getDeliveryAddress(): DeliveryAddress {
  if (typeof window === "undefined") return DEFAULT_DELIVERY_ADDRESS;
  const raw = localStorage.getItem(ADDRESS_KEY);
  if (!raw) return DEFAULT_DELIVERY_ADDRESS;
  try {
    return { ...DEFAULT_DELIVERY_ADDRESS, ...(JSON.parse(raw) as DeliveryAddress) };
  } catch {
    return DEFAULT_DELIVERY_ADDRESS;
  }
}

export function setDeliveryAddress(address: DeliveryAddress) {
  localStorage.setItem(ADDRESS_KEY, JSON.stringify(address));
}

export function setSession(token: string, tenantId: string) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(TENANT_KEY, tenantId);
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(CART_KEY);
}

export function getSessionCart(): SessionCart | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(CART_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw) as SessionCart;
  } catch {
    return null;
  }
}

export function setSessionCart(cart: SessionCart | null) {
  if (!cart) {
    localStorage.removeItem(CART_KEY);
    return;
  }
  localStorage.setItem(CART_KEY, JSON.stringify(cart));
}

export function api() {
  return createApiClient({
    getTenantId,
    getAccessToken: async () => getToken(),
  });
}
