"use client";

import { createApiClient } from "@commerce/api-client";

const TOKEN_KEY = "ce_customer_token";
const TENANT_KEY = "ce_customer_tenant";
const CART_KEY = "ce_customer_cart";

export type SessionCart = {
  cartId: string;
  businessId: string;
  locationId?: string | null;
};

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getTenantId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TENANT_KEY) || process.env.NEXT_PUBLIC_TENANT_ID || null;
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
