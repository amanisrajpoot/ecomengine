/** Thin fetch wrapper against the Commerce Engine API. */

import type {
  Addon,
  Business,
  BusinessLocation,
  Cart,
  CourierQuote,
  Delivery,
  Fulfillment,
  InventoryItem,
  NearbyStore,
  Order,
  OrderDebugger,
  Partner,
  Product,
  ProductAddonLink,
  Settlement,
  StockMovement,
  Refund,
  Notification,
  Payment,
  PaymentInitiateResponse,
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
      body: {
        variant_id: string;
        quantity?: number;
        addons?: Array<{ addon_id: string; quantity?: number }>;
      },
    ) =>
      request<Cart>(`/api/v1/carts/${cartId}/items`, {
        method: "POST",
        body: JSON.stringify(body),
      }),

    updateCartItem: (cartId: string, itemId: string, body: { quantity: number }) =>
      request<Cart>(`/api/v1/carts/${cartId}/items/${itemId}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),

    removeCartItem: (cartId: string, itemId: string) =>
      request<Cart>(`/api/v1/carts/${cartId}/items/${itemId}`, {
        method: "DELETE",
      }),

    listAddons: (businessId: string) =>
      request<Addon[]>(`/api/v1/businesses/${businessId}/addons`),

    listProductAddons: (businessId: string, productId: string) =>
      request<ProductAddonLink[]>(
        `/api/v1/businesses/${businessId}/products/${productId}/addons`,
      ),

    checkout: (body: {
      cart_id: string;
      payment_provider?: string;
      fulfillment_type?: string;
      customer_phone?: string;
      return_url?: string;
      delivery_address?: {
        line1: string;
        city: string;
        state?: string;
        pincode: string;
        lat?: number;
        lng?: number;
      };
    }) =>
      request<Order>("/api/v1/orders/checkout", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    listOrders: (params?: { business_id?: string; status?: string; mine?: boolean }) =>
      request<Order[]>(`/api/v1/orders${toQuery(params ?? {})}`),

    getOrder: (orderId: string) => request<Order>(`/api/v1/orders/${orderId}`),

    transitionOrder: (
      orderId: string,
      body: { to_status: string; actor?: string; reason?: string },
    ) =>
      request<Order>(`/api/v1/orders/${orderId}/transitions`, {
        method: "POST",
        body: JSON.stringify({ actor: body.actor ?? "system", ...body }),
      }),

    listBusinesses: (params?: { status?: string; type?: string }) =>
      request<Business[]>(`/api/v1/businesses${toQuery(params ?? {})}`),

    listLocations: (businessId: string, activeOnly = true) =>
      request<BusinessLocation[]>(
        `/api/v1/businesses/${businessId}/locations${toQuery({ active_only: activeOnly })}`,
      ),

    upsertInventoryItem: (
      businessId: string,
      body: {
        location_id: string;
        variant_id: string;
        low_stock_threshold?: number;
      },
    ) =>
      request<InventoryItem>(`/api/v1/businesses/${businessId}/inventory`, {
        method: "POST",
        body: JSON.stringify(body),
      }),

    listInventory: (
      businessId: string,
      params?: {
        location_id?: string;
        low_stock_only?: boolean;
        out_of_stock_only?: boolean;
      },
    ) =>
      request<InventoryItem[]>(
        `/api/v1/businesses/${businessId}/inventory${toQuery(params ?? {})}`,
      ),

    getInventoryItem: (businessId: string, itemId: string) =>
      request<InventoryItem>(
        `/api/v1/businesses/${businessId}/inventory/${itemId}`,
      ),

    adjustInventory: (
      businessId: string,
      itemId: string,
      body: {
        delta_on_hand: number;
        reason?: string;
        note?: string;
      },
    ) =>
      request<InventoryItem>(
        `/api/v1/businesses/${businessId}/inventory/${itemId}/adjust`,
        {
          method: "POST",
          body: JSON.stringify(body),
        },
      ),

    listInventoryMovements: (businessId: string, itemId: string) =>
      request<StockMovement[]>(
        `/api/v1/businesses/${businessId}/inventory/${itemId}/movements`,
      ),

    listSettlements: (params?: {
      party_type?: string;
      party_id?: string;
      status?: string;
    }) => request<Settlement[]>(`/api/v1/settlements${toQuery(params ?? {})}`),

    getSettlement: (settlementId: string) =>
      request<Settlement>(`/api/v1/settlements/${settlementId}`),

    createSettlement: (body: {
      party_type: string;
      party_id: string;
      period_start: string;
      period_end: string;
      currency?: string;
    }) =>
      request<Settlement>("/api/v1/settlements", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    calculateSettlement: (settlementId: string) =>
      request<Settlement>(`/api/v1/settlements/${settlementId}/calculate`, {
        method: "POST",
      }),

    reconcileSettlement: (settlementId: string) =>
      request<Settlement>(`/api/v1/settlements/${settlementId}/reconcile`, {
        method: "POST",
      }),

    approveSettlement: (settlementId: string, body?: { reason?: string }) =>
      request<Settlement>(`/api/v1/settlements/${settlementId}/approve`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }),

    markSettlementPaid: (settlementId: string, body?: { reason?: string }) =>
      request<Settlement>(`/api/v1/settlements/${settlementId}/mark-paid`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }),

    listOrderSettlements: (orderId: string) =>
      request<Settlement[]>(`/api/v1/orders/${orderId}/settlements`),

    listPaymentProviders: () =>
      request<{ providers: string[] }>("/api/v1/payments/providers"),

    listOrderPayments: (orderId: string) =>
      request<Payment[]>(`/api/v1/orders/${orderId}/payments`),

    initiateOrderPayment: (
      orderId: string,
      body?: {
        provider?: string;
        return_url?: string;
        customer_phone?: string;
        customer_email?: string;
      },
    ) =>
      request<PaymentInitiateResponse>(`/api/v1/orders/${orderId}/payments`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }),

    verifyOrderPayment: (
      orderId: string,
      body?: { provider?: string; provider_ref?: string },
    ) =>
      request<PaymentInitiateResponse>(`/api/v1/orders/${orderId}/payments/verify`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }),

    refundPayment: (
      paymentId: string,
      body: { amount_paise: number; reason?: string },
    ) =>
      request<Refund>(`/api/v1/payments/${paymentId}/refunds`, {
        method: "POST",
        body: JSON.stringify(body),
      }),

    listNotifications: (params?: { order_id?: string; limit?: number }) =>
      request<Notification[]>(`/api/v1/notifications${toQuery(params ?? {})}`),

    getOrderFulfillment: (orderId: string) =>
      request<Fulfillment>(`/api/v1/orders/${orderId}/fulfillment`),

    createDelivery: (fulfillmentId: string, body?: Record<string, unknown>) =>
      request<Delivery>(`/api/v1/fulfillments/${fulfillmentId}/deliveries`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }),

    getFulfillmentDelivery: (fulfillmentId: string) =>
      request<Delivery>(`/api/v1/fulfillments/${fulfillmentId}/delivery`),

    assignDelivery: (deliveryId: string, body?: { partner_id?: string }) =>
      request<Delivery>(`/api/v1/deliveries/${deliveryId}/assign`, {
        method: "POST",
        body: JSON.stringify(body ?? {}),
      }),

    listDeliveryPartners: (params?: { online_only?: boolean; status?: string }) =>
      request<Partner[]>(`/api/v1/delivery-partners${toQuery(params ?? {})}`),

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
