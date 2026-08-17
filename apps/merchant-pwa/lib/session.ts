const ACCESS_TOKEN_KEY = "merchant_access_token";
const TENANT_ID_KEY = "merchant_tenant_id";
const BUSINESS_ID_KEY = "merchant_business_id";

function read(key: string): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(key);
}

function write(key: string, value: string | null) {
  if (typeof window === "undefined") return;
  if (value === null) {
    localStorage.removeItem(key);
  } else {
    localStorage.setItem(key, value);
  }
}

export const session = {
  getAccessToken: () => read(ACCESS_TOKEN_KEY),
  setAccessToken: (token: string | null) => write(ACCESS_TOKEN_KEY, token),

  getTenantId: () => read(TENANT_ID_KEY),
  setTenantId: (tenantId: string | null) => write(TENANT_ID_KEY, tenantId),

  getActiveBusinessId: () => read(BUSINESS_ID_KEY),
  setActiveBusinessId: (businessId: string | null) => write(BUSINESS_ID_KEY, businessId),

  clearAuth: () => {
    write(ACCESS_TOKEN_KEY, null);
  },
};
