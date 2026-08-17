"use client";

import { useEffect, useState } from "react";

import { ApiError } from "@commerce/api-client";
import { Button, Card, Input } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export default function SettingsPage() {
  const [tenantId, setTenantId] = useState("");
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [roles, setRoles] = useState<string[]>([]);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setTenantId(session.getTenantId() ?? "");
    if (!session.getAccessToken()) return;
    getApiClient()
      .me()
      .then((user) => {
        setUserEmail(user.email);
        setRoles(user.roles.map((r) => r.role));
      })
      .catch(() => {
        setUserEmail(null);
        setRoles([]);
      });
  }, []);

  function saveTenant() {
    const trimmed = tenantId.trim();
    session.setTenantId(trimmed || null);
    setMessage(trimmed ? "Tenant context saved." : "Tenant context cleared (platform scope).");
    setError(null);
  }

  async function checkApi() {
    try {
      const meta = await getApiClient().getMeta();
      setMessage(`API ${meta.name} v${meta.version}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "API unreachable");
    }
  }

  function signOut() {
    session.clearAuth();
    setUserEmail(null);
    setRoles([]);
    setMessage("Signed out.");
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <Card title="Tenant context">
        <p className="mb-3 text-sm text-violet-200/70">
          Super admin can omit tenant. Tenant admins set X-Tenant-ID for scoped APIs.
        </p>
        <Input label="Tenant ID" value={tenantId} onChange={(e) => setTenantId(e.target.value)} />
        <div className="mt-3 flex gap-2">
          <Button onClick={saveTenant}>Save</Button>
          <Button variant="secondary" onClick={checkApi}>Check API</Button>
        </div>
      </Card>
      <Card title="Session">
        <p className="text-sm">{userEmail ? `Signed in as ${userEmail}` : "Not signed in"}</p>
        {roles.length > 0 ? (
          <p className="mt-1 text-xs text-violet-300/70">Roles: {roles.join(", ")}</p>
        ) : null}
        <Button variant="secondary" className="mt-3" onClick={signOut}>Sign out</Button>
      </Card>
      {message ? <p className="text-sm text-emerald-300">{message}</p> : null}
      {error ? <p className="text-sm text-red-300">{error}</p> : null}
    </div>
  );
}
