/** Thin fetch wrapper against the Commerce Engine API. */

import type {
  Addon,
  Bundle,
  Business,
  BusinessLocation,
  Category,
  InventoryItem,
  Product,
  ProductAddonLink,
  StockMovement,
  Tenant,
  TokenResponse,
  User,
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

    listBusinesses: (params?: { status?: string; type?: string }) => {
      const search = new URLSearchParams();
      if (params?.status) search.set("status", params.status);
      if (params?.type) search.set("type", params.type);
      const qs = search.toString();
      return request<Business[]>(`/api/v1/businesses${qs ? `?${qs}` : ""}`);
    },

    createBusiness: (body: {
      name: string;
      type?: string;
      description?: string;
      logo_url?: string;
      contact?: Record<string, unknown>;
      settings?: Record<string, unknown>;
      capabilities?: Record<string, boolean>;
      status?: string;
    }) =>
      request<Business>("/api/v1/businesses", {
        method: "POST",
        body: JSON.stringify(body),
      }),

    getBusiness: (businessId: string) =>
      request<Business>(`/api/v1/businesses/${businessId}`),

    updateBusiness: (
      businessId: string,
      body: {
        name?: string;
        description?: string;
        logo_url?: string;
        contact?: Record<string, unknown>;
        settings?: Record<string, unknown>;
        capabilities?: Record<string, boolean>;
        status?: string;
      },
    ) =>
      request<Business>(`/api/v1/businesses/${businessId}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),

    listLocations: (businessId: string, activeOnly = true) =>
      request<BusinessLocation[]>(
        `/api/v1/businesses/${businessId}/locations?active_only=${activeOnly}`,
      ),

    createLocation: (
      businessId: string,
      body: {
        name: string;
        address: Record<string, unknown>;
        lat: number;
        lng: number;
        hours?: Record<string, unknown>[];
        timezone?: string;
        is_active?: boolean;
        service_area?: Record<string, unknown>;
      },
    ) =>
      request<BusinessLocation>(`/api/v1/businesses/${businessId}/locations`, {
        method: "POST",
        body: JSON.stringify(body),
      }),

    getLocation: (businessId: string, locationId: string) =>
      request<BusinessLocation>(
        `/api/v1/businesses/${businessId}/locations/${locationId}`,
      ),

    updateLocation: (
      businessId: string,
      locationId: string,
      body: {
        name?: string;
        address?: Record<string, unknown>;
        lat?: number;
        lng?: number;
        hours?: Record<string, unknown>[];
        timezone?: string;
        is_active?: boolean;
        service_area?: Record<string, unknown>;
      },
    ) =>
      request<BusinessLocation>(
        `/api/v1/businesses/${businessId}/locations/${locationId}`,
        {
          method: "PATCH",
          body: JSON.stringify(body),
        },
      ),

    listCategories: (businessId: string, activeOnly = true) =>
      request<Category[]>(
        `/api/v1/businesses/${businessId}/categories?active_only=${activeOnly}`,
      ),

    createCategory: (
      businessId: string,
      body: {
        name: string;
        parent_id?: string;
        sort_order?: number;
        is_active?: boolean;
      },
    ) =>
      request<Category>(`/api/v1/businesses/${businessId}/categories`, {
        method: "POST",
        body: JSON.stringify(body),
      }),

    updateCategory: (
      businessId: string,
      categoryId: string,
      body: {
        name?: string;
        parent_id?: string;
        sort_order?: number;
        is_active?: boolean;
      },
    ) =>
      request<Category>(`/api/v1/businesses/${businessId}/categories/${categoryId}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),

    listProducts: (
      businessId: string,
      params?: { category_id?: string; active_only?: boolean },
    ) => {
      const search = new URLSearchParams();
      if (params?.category_id) search.set("category_id", params.category_id);
      if (params?.active_only !== undefined) {
        search.set("active_only", String(params.active_only));
      }
      const qs = search.toString();
      return request<Product[]>(
        `/api/v1/businesses/${businessId}/products${qs ? `?${qs}` : ""}`,
      );
    },

    createProduct: (
      businessId: string,
      body: {
        name: string;
        category_id?: string;
        description?: string;
        images?: string[];
        tags?: string[];
        is_active?: boolean;
      },
    ) =>
      request<Product>(`/api/v1/businesses/${businessId}/products`, {
        method: "POST",
        body: JSON.stringify(body),
      }),

    getProduct: (businessId: string, productId: string) =>
      request<Product>(`/api/v1/businesses/${businessId}/products/${productId}`),

    updateProduct: (
      businessId: string,
      productId: string,
      body: {
        name?: string;
        category_id?: string;
        description?: string;
        images?: string[];
        tags?: string[];
        is_active?: boolean;
      },
    ) =>
      request<Product>(`/api/v1/businesses/${businessId}/products/${productId}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),

    listVariants: (businessId: string, productId: string, availableOnly = true) =>
      request<Variant[]>(
        `/api/v1/businesses/${businessId}/products/${productId}/variants?available_only=${availableOnly}`,
      ),

    createVariant: (
      businessId: string,
      productId: string,
      body: {
        name: string;
        sku?: string;
        base_price_paise: number;
        is_available?: boolean;
        meta?: Record<string, unknown>;
      },
    ) =>
      request<Variant>(
        `/api/v1/businesses/${businessId}/products/${productId}/variants`,
        {
          method: "POST",
          body: JSON.stringify(body),
        },
      ),

    updateVariant: (
      businessId: string,
      productId: string,
      variantId: string,
      body: {
        name?: string;
        sku?: string;
        base_price_paise?: number;
        is_available?: boolean;
        meta?: Record<string, unknown>;
      },
    ) =>
      request<Variant>(
        `/api/v1/businesses/${businessId}/products/${productId}/variants/${variantId}`,
        {
          method: "PATCH",
          body: JSON.stringify(body),
        },
      ),

    listAddons: (businessId: string, activeOnly = true) =>
      request<Addon[]>(
        `/api/v1/businesses/${businessId}/addons?active_only=${activeOnly}`,
      ),

    createAddon: (
      businessId: string,
      body: { name: string; price_paise: number; max_qty?: number; is_active?: boolean },
    ) =>
      request<Addon>(`/api/v1/businesses/${businessId}/addons`, {
        method: "POST",
        body: JSON.stringify(body),
      }),

    updateAddon: (
      businessId: string,
      addonId: string,
      body: { name?: string; price_paise?: number; max_qty?: number; is_active?: boolean },
    ) =>
      request<Addon>(`/api/v1/businesses/${businessId}/addons/${addonId}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),

    linkProductAddon: (
      businessId: string,
      productId: string,
      body: { addon_id: string; group_name?: string; is_required?: boolean },
    ) =>
      request<ProductAddonLink>(
        `/api/v1/businesses/${businessId}/products/${productId}/addon-links`,
        {
          method: "POST",
          body: JSON.stringify(body),
        },
      ),

    listProductAddonLinks: (businessId: string, productId: string) =>
      request<ProductAddonLink[]>(
        `/api/v1/businesses/${businessId}/products/${productId}/addon-links`,
      ),

    listBundles: (businessId: string, activeOnly = true) =>
      request<Bundle[]>(
        `/api/v1/businesses/${businessId}/bundles?active_only=${activeOnly}`,
      ),

    createBundle: (
      businessId: string,
      body: {
        name: string;
        price_paise?: number;
        items?: { variant_id: string; quantity?: number }[];
        is_active?: boolean;
      },
    ) =>
      request<Bundle>(`/api/v1/businesses/${businessId}/bundles`, {
        method: "POST",
        body: JSON.stringify(body),
      }),

    updateBundle: (
      businessId: string,
      bundleId: string,
      body: {
        name?: string;
        price_paise?: number;
        items?: { variant_id: string; quantity?: number }[];
        is_active?: boolean;
      },
    ) =>
      request<Bundle>(`/api/v1/businesses/${businessId}/bundles/${bundleId}`, {
        method: "PATCH",
        body: JSON.stringify(body),
      }),

    listInventoryItems: (businessId: string, locationId: string) =>
      request<InventoryItem[]>(
        `/api/v1/businesses/${businessId}/locations/${locationId}/inventory-items`,
      ),

    createInventoryItem: (
      businessId: string,
      locationId: string,
      body: {
        variant_id: string;
        on_hand?: number;
        reserved?: number;
        low_stock_threshold?: number;
      },
    ) =>
      request<InventoryItem>(
        `/api/v1/businesses/${businessId}/locations/${locationId}/inventory-items`,
        {
          method: "POST",
          body: JSON.stringify(body),
        },
      ),

    getInventoryItem: (businessId: string, locationId: string, inventoryItemId: string) =>
      request<InventoryItem>(
        `/api/v1/businesses/${businessId}/locations/${locationId}/inventory-items/${inventoryItemId}`,
      ),

    updateInventoryItem: (
      businessId: string,
      locationId: string,
      inventoryItemId: string,
      body: { low_stock_threshold?: number },
    ) =>
      request<InventoryItem>(
        `/api/v1/businesses/${businessId}/locations/${locationId}/inventory-items/${inventoryItemId}`,
        {
          method: "PATCH",
          body: JSON.stringify(body),
        },
      ),

    adjustStock: (
      businessId: string,
      locationId: string,
      inventoryItemId: string,
      body: {
        delta_on_hand?: number;
        delta_reserved?: number;
        reason?: string;
        reference_type?: string;
        reference_id?: string;
      },
    ) =>
      request<InventoryItem>(
        `/api/v1/businesses/${businessId}/locations/${locationId}/inventory-items/${inventoryItemId}/adjust`,
        {
          method: "POST",
          body: JSON.stringify(body),
        },
      ),

    reserveStock: (
      businessId: string,
      locationId: string,
      inventoryItemId: string,
      body: { quantity: number; reason?: string; reference_type?: string; reference_id?: string },
    ) =>
      request<InventoryItem>(
        `/api/v1/businesses/${businessId}/locations/${locationId}/inventory-items/${inventoryItemId}/reserve`,
        {
          method: "POST",
          body: JSON.stringify(body),
        },
      ),

    releaseStock: (
      businessId: string,
      locationId: string,
      inventoryItemId: string,
      body: { quantity: number; reason?: string; reference_type?: string; reference_id?: string },
    ) =>
      request<InventoryItem>(
        `/api/v1/businesses/${businessId}/locations/${locationId}/inventory-items/${inventoryItemId}/release`,
        {
          method: "POST",
          body: JSON.stringify(body),
        },
      ),

    listStockMovements: (
      businessId: string,
      locationId: string,
      inventoryItemId: string,
    ) =>
      request<StockMovement[]>(
        `/api/v1/businesses/${businessId}/locations/${locationId}/inventory-items/${inventoryItemId}/movements`,
      ),

    listLowStock: (businessId: string) =>
      request<InventoryItem[]>(`/api/v1/businesses/${businessId}/inventory/low-stock`),
  };
}

export type ApiClient = ReturnType<typeof createApiClient>;
