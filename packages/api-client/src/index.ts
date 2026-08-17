/** Thin fetch wrapper against the Commerce Engine API. */

import type { Tenant, TokenResponse, User } from "@commerce/types";

export type ApiClientOptions = {
  baseUrl?: string;
  getTenantId?: () => string | null;
  getAccessToken?: () => string | null | Promise<string | null>;
  /** @deprecated prefer getTenantId */
  tenantId?: string;
};

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

export function createApiClient(options: ApiClientOptions = {}) {
  const baseUrl = options.baseUrl ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  function tenantHeaders(): Record<string, string> {
    const tid = options.getTenantId?.() ?? options.tenantId;
    return tid ? { "X-Tenant-ID": tid } : {};
  }

  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    for (const [key, value] of Object.entries(tenantHeaders())) {
      headers.set(key, value);
    }
    const token = options.getAccessToken ? await options.getAccessToken() : null;
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(`${baseUrl}${path}`, { ...init, headers });
    if (!response.ok) {
      let code = "HTTP_ERROR";
      let message = response.statusText;
      try {
        const body = (await response.json()) as {
          error?: { code?: string; message?: string };
        };
        code = body.error?.code ?? code;
        message = body.error?.message ?? message;
      } catch {
        // ignore JSON parse errors
      }
      throw new ApiError(response.status, code, message);
    }
    if (response.status === 204) {
      return undefined as T;
    }
    return (await response.json()) as T;
  }

  return {
    getHealth: () => request<{ status: string }>("/health"),

    getMeta: () =>
      request<{ name: string; version: string; environment: string }>("/api/v1/meta"),

    login: (body: { email: string; password: string }) =>
      request<TokenResponse>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    register: (body: { email: string; password: string; display_name?: string }) =>
      request<TokenResponse>("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    requestOtp: (body: { phone: string }) =>
      request<{ message: string; expires_in_seconds: number; debug_code?: string }>(
        "/api/v1/auth/otp/request",
        { method: "POST", body: JSON.stringify(body) },
      ),

    verifyOtp: (body: { phone: string; code: string }) =>
      request<TokenResponse>("/api/v1/auth/otp/verify", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    me: () => request<User>("/api/v1/auth/me"),

    listTenants: () => request<Tenant[]>("/api/v1/tenants"),

    createTenant: (body: { name: string; slug: string; config?: Record<string, unknown> }) =>
      request<Tenant>("/api/v1/tenants", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    getTenant: (tenantId: string) => request<Tenant>(`/api/v1/tenants/${tenantId}`),

    updateTenant: (
      tenantId: string,
      body: { name?: string; status?: string; config?: Record<string, unknown> },
    ) =>
      request<Tenant>(`/api/v1/tenants/${tenantId}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),
  };
}

export type ApiClient = ReturnType<typeof createApiClient>;
