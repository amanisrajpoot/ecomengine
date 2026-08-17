"use client";

import { useState } from "react";

import { ApiError } from "@commerce/api-client";
import { Button, Card, Input } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

const ROLES = [
  "TENANT_ADMIN",
  "BUSINESS_OWNER",
  "DELIVERY_PARTNER",
  "CUSTOMER",
  "STAFF",
  "BUSINESS_MANAGER",
];

export default function AssignRolePage() {
  const [userId, setUserId] = useState("");
  const [role, setRole] = useState("DELIVERY_PARTNER");
  const [tenantId, setTenantId] = useState(session.getTenantId() ?? "");
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setLoading(true);
    setMessage(null);
    setError(null);
    try {
      const binding = await getApiClient().assignUserRole(userId.trim(), {
        role,
        tenant_id: tenantId.trim() || undefined,
      });
      setMessage(`Assigned ${binding.role} to user ${binding.user_id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Role assignment failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Assign role</h1>
      <p className="text-sm text-violet-200/70">
        Grant roles such as <code>DELIVERY_PARTNER</code> after a user registers. Requires admin
        permission.
      </p>
      <Card>
        <form className="space-y-3" onSubmit={onSubmit}>
          <Input
            label="User ID"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
            required
          />
          <label className="flex flex-col gap-1.5 text-sm">
            <span className="text-emerald-200/80">Role</span>
            <select
              className="rounded-lg border border-emerald-700/40 bg-emerald-950/60 px-3 py-2"
              value={role}
              onChange={(e) => setRole(e.target.value)}
            >
              {ROLES.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
          </label>
          <Input
            label="Tenant ID"
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
            required
          />
          <Button type="submit" disabled={loading || !userId.trim()}>
            {loading ? "Assigning…" : "Assign role"}
          </Button>
        </form>
      </Card>
      {message ? <p className="text-sm text-emerald-300">{message}</p> : null}
      {error ? <p className="text-sm text-red-300">{error}</p> : null}
    </div>
  );
}
