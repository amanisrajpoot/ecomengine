/** Thin fetch wrapper against the Commerce Engine API. */

import type {
  Business,
  Cart,
  CourierQuote,
  Delivery,
  Fulfillment,
  NearbyStore,
  Order,
  OrderDebugger,
  Partner,
  Product,
  TokenResponse,
  Tenant,
  Variant,
} from "@commerce/types";

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

function toQuery(params: Record<string, string | number | boolean | undefined | null>): string {
  const q = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value === undefined || value === null || value === "") continue;
    q.set(key, String(value));
  }
  const s = q.toString();
  return s ? `?${s}` : "";
}

export function createApiClient(options: ApiClientOptions = {}) {
  const baseUrl = options.baseUrl ?? process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

  async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    if (init.body && !headers.has("Content-Type")) {
      headers.set("Content-Type", "application/json");
    }
    const tenantId = options.getTenantId?.() ?? options.tenantId ?? null;
    if (tenantId) {
      headers.set("X-Tenant-ID", tenantId);
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

    listTenants: () => request<Tenant[]>("/api/v1/tenants"),

    getOrderDebugger: (orderId: string) =>
      request<OrderDebugger>(`/api/v1/orders/${orderId}/debugger`),

    login: (body: { email: string; password: string }) =>
      request<TokenResponse>("/api/v1/auth/login", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    register: (body: {
      email: string;
      password: string;
      display_name?: string;
    }) =>
      request<TokenResponse>("/api/v1/auth/register", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    me: () =>
      request<{
        id: string;
        email: string | null;
        display_name: string | null;
      }>("/api/v1/auth/me"),

    nearbyStores: (params: {
      lat: number;
      lng: number;
      radius_km?: number;
      type?: string;
      limit?: number;
    }) =>
      request<NearbyStore[]>(
        `/api/v1/stores/nearby${toQuery(params)}`,
      ),

    getBusiness: (businessId: string) =>
      request<{
        id: string;
        name: string;
        type: string;
        capabilities: Record<string, unknown>;
      }>(`/api/v1/businesses/${businessId}`),

    listProducts: (businessId: string, activeOnly = true) =>
      request<Product[]>(
        `/api/v1/businesses/${businessId}/products${toQuery({ active_only: activeOnly })}`,
      ),

    listVariants: (businessId: string, productId: string) =>
      request<Variant[]>(
        `/api/v1/businesses/${businessId}/products/${productId}/variants`,
      ),

    createCart: (body: {
      business_id: string;
      location_id?: string | null;
      delivery_fee_paise?: number;
      platform_fee_paise?: number;
    }) =>
      request<Cart>("/api/v1/carts", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    getCart: (cartId: string) => request<Cart>(`/api/v1/carts/${cartId}`),

    addCartItem: (
      cartId: string,
      body: { variant_id: string; quantity?: number; addons?: unknown[] },
    ) =>
      request<Cart>(`/api/v1/carts/${cartId}/items`, {
        method: "POST",
        body: JSON.stringify(body),
      }),

    checkout: (body: {
      cart_id: string;
      payment_provider?: string;
      fulfillment_type?: string;
      customer_phone?: string;
    }) =>
      request<Order>("/api/v1/orders/checkout", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    listOrders: (params?: { business_id?: string; status?: string }) =>
      request<Order[]>(`/api/v1/orders${toQuery(params ?? {})}`),

    getOrder: (orderId: string) => request<Order>(`/api/v1/orders/${orderId}`),

    transitionOrder: (
      orderId: string,
      body: { to_status: string; actor?: string; reason?: string },
    ) =>
      request<Order>(`/api/v1/orders/${orderId}/transitions`, {
        method: "POST",
        body: JSON.stringify({ actor: "merchant", ...body }),
      }),

    listBusinesses: (params?: { status?: string; type?: string }) =>
      request<Business[]>(`/api/v1/businesses${toQuery(params ?? {})}`),

    getOrderFulfillment: (orderId: string) =>
      request<Fulfillment>(`/api/v1/orders/${orderId}/fulfillment`),

    courierQuote: (body: Record<string, unknown>) =>
      request<CourierQuote>("/api/v1/courier/quote", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    createShipment: (body: Record<string, unknown>) =>
      request<Order>("/api/v1/courier/shipments", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    getMyPartner: () => request<Partner>("/api/v1/delivery-partners/me"),

    updateMyLocation: (body: { lat: number; lng: number; is_online?: boolean }) =>
      request<Partner>("/api/v1/delivery-partners/me/location", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    listDeliveries: (params?: {
      mine?: boolean;
      partner_id?: string;
      status?: string;
      active_only?: boolean;
    }) => request<Delivery[]>(`/api/v1/deliveries${toQuery(params ?? {})}`),

    getDelivery: (deliveryId: string) =>
      request<Delivery>(`/api/v1/deliveries/${deliveryId}`),

    completeDeliveryStop: (
      deliveryId: string,
      stopId: string,
      proof?: Record<string, unknown>,
    ) =>
      request<Delivery>(
        `/api/v1/deliveries/${deliveryId}/stops/${stopId}/complete`,
        {
          method: "POST",
          body: JSON.stringify({ proof: proof ?? {} }),
        },
      ),

    updateDeliveryTracking: (
      deliveryId: string,
      body: { lat: number; lng: number; heading?: number; speed_kmh?: number },
    ) =>
      request<Delivery>(`/api/v1/deliveries/${deliveryId}/tracking`, {
        method: "POST",
        body: JSON.stringify(body),
      }),
  };
}

export type ApiClient = ReturnType<typeof createApiClient>;
