"use client";

import { createApiClient } from "@commerce/api-client";

const TOKEN_KEY = "ce_rider_token";
const TENANT_KEY = "ce_rider_tenant";

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
}

export function api() {
  return createApiClient({
    getTenantId,
    getAccessToken: async () => getToken(),
  });
}

/** Demo coordinates — Indiranagar area. */
export const DEMO_LAT = 12.9784;
export const DEMO_LNG = 77.6408;
