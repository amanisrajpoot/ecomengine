"use client";

import { useEffect, useState } from "react";

import { ApiError } from "@commerce/api-client";
import { Button, Card, Input } from "@commerce/ui";

import { getApiClient } from "@/lib/api";
import { session } from "@/lib/session";

export default function SettingsPage() {
  const [tenantId, setTenantId] = useState("");
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [message, setMessage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setTenantId(session.getTenantId() ?? "");
    const token = session.getAccessToken();
    if (!token) return;

    getApiClient()
      .me()
      .then((user) => setUserEmail(user.email))
      .catch(() => setUserEmail(null));
  }, []);

  async function saveTenant() {
    setError(null);
    setMessage(null);
    const trimmed = tenantId.trim();
    if (!trimmed) {
      setError("Tenant ID is required for API calls.");
      return;
    }
    session.setTenantId(trimmed);
    setMessage("Tenant ID saved.");
  }

  async function checkApi() {
    setError(null);
    setMessage(null);
    try {
      const meta = await getApiClient().getMeta();
      setMessage(`API ${meta.name} v${meta.version} (${meta.environment})`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not reach API");
    }
  }

  function signOut() {
    session.clearAuth();
    session.clearCart();
    setUserEmail(null);
    setMessage("Signed out.");
  }

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-emerald-200/70">
          Set tenant context before login or register. Use the tenant ID from your platform admin.
        </p>
      </div>

      <Card title="Tenant">
        <div className="space-y-3">
          <Input
            label="Tenant ID"
            value={tenantId}
            onChange={(e) => setTenantId(e.target.value)}
            placeholder="uuid from admin / docker seed"
          />
          <div className="flex flex-wrap gap-2">
            <Button onClick={saveTenant}>Save tenant</Button>
            <Button variant="secondary" onClick={checkApi}>Check API</Button>
          </div>
        </div>
      </Card>

      <Card title="Session">
        <p className="text-sm text-emerald-200/80">
          {userEmail ? `Signed in as ${userEmail}` : "Not signed in"}
        </p>
        <div className="mt-3 flex flex-wrap gap-2">
          <Button variant="secondary" onClick={signOut}>Sign out</Button>
        </div>
      </Card>

      {message ? <p className="text-sm text-emerald-300">{message}</p> : null}
      {error ? <p className="text-sm text-red-300">{error}</p> : null}
    </div>
  );
}
