import type { APIRequestContext } from "@playwright/test";

const API_BASE = process.env.E2E_API_URL ?? "http://127.0.0.1:8000";

export type SeededTenant = {
  tenantId: string;
  businessId: string;
  businessName: string;
  slug: string;
};

export async function seedActiveFoodStore(
  request: APIRequestContext,
  slug: string,
): Promise<SeededTenant> {
  const login = await request.post(`${API_BASE}/api/v1/auth/login`, {
    data: { email: "admin@example.com", password: "ChangeMe123!" },
  });
  if (!login.ok()) {
    throw new Error(`Admin login failed: ${login.status()} ${await login.text()}`);
  }
  const { access_token: adminToken } = await login.json();

  const tenantRes = await request.post(`${API_BASE}/api/v1/tenants`, {
    headers: { Authorization: `Bearer ${adminToken}` },
    data: { name: `E2E ${slug}`, slug },
  });
  if (!tenantRes.ok()) {
    throw new Error(`Tenant create failed: ${tenantRes.status()} ${await tenantRes.text()}`);
  }
  const tenantId = (await tenantRes.json()).id as string;

  const businessName = "E2E Kitchen";
  const businessRes = await request.post(`${API_BASE}/api/v1/businesses`, {
    headers: {
      Authorization: `Bearer ${adminToken}`,
      "X-Tenant-ID": tenantId,
    },
    data: { name: businessName, type: "FOOD", status: "ACTIVE" },
  });
  if (!businessRes.ok()) {
    throw new Error(`Business create failed: ${businessRes.status()} ${await businessRes.text()}`);
  }
  const businessId = (await businessRes.json()).id as string;

  return { tenantId, businessId, businessName, slug };
}
