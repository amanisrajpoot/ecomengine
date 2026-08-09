"use client";

import { createApiClient } from "@commerce/api-client";

const TOKEN_KEY = "ce_merchant_token";
const TENANT_KEY = "ce_merchant_tenant";
const BUSINESS_KEY = "ce_merchant_business";
const LOCATION_KEY = "ce_merchant_location";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getTenantId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TENANT_KEY) || process.env.NEXT_PUBLIC_TENANT_ID || null;
}

export function getBusinessId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(BUSINESS_KEY);
}

export function setSession(token: string, tenantId: string) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(TENANT_KEY, tenantId);
}

export function setBusinessId(businessId: string | null) {
  if (!businessId) localStorage.removeItem(BUSINESS_KEY);
  else localStorage.setItem(BUSINESS_KEY, businessId);
}

export function getLocationId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(LOCATION_KEY);
}

export function setLocationId(locationId: string | null) {
  if (!locationId) localStorage.removeItem(LOCATION_KEY);
  else localStorage.setItem(LOCATION_KEY, locationId);
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(BUSINESS_KEY);
  localStorage.removeItem(LOCATION_KEY);
}

export function api() {
  return createApiClient({
    getTenantId,
    getAccessToken: async () => getToken(),
  });
}
