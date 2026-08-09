"use client";

import { createApiClient } from "@commerce/api-client";

const TOKEN_KEY = "ce_admin_token";
const TENANT_KEY = "ce_admin_tenant";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getTenantId(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TENANT_KEY) || process.env.NEXT_PUBLIC_TENANT_ID || null;
}

export function setSession(token: string, tenantId?: string | null) {
  localStorage.setItem(TOKEN_KEY, token);
  if (tenantId) localStorage.setItem(TENANT_KEY, tenantId);
}

export function setTenantId(tenantId: string | null) {
  if (!tenantId) localStorage.removeItem(TENANT_KEY);
  else localStorage.setItem(TENANT_KEY, tenantId);
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(TENANT_KEY);
}

export function api() {
  return createApiClient({
    getTenantId,
    getAccessToken: async () => getToken(),
  });
}
