/** Shared domain primitives. */

export type TenantId = string;
export type UserId = string;

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user_id: UserId;
  tenant_id: TenantId | null;
}

export interface RoleBinding {
  id: string;
  user_id: UserId;
  role: string;
  tenant_id: TenantId | null;
  business_id: string | null;
  created_at: string;
}

export interface User {
  id: UserId;
  tenant_id: TenantId | null;
  email: string | null;
  phone: string | null;
  status: string;
  display_name: string | null;
  created_at: string;
  updated_at: string;
  roles: RoleBinding[];
}

export interface Tenant {
  id: TenantId;
  name: string;
  slug: string;
  status: string;
  config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}
