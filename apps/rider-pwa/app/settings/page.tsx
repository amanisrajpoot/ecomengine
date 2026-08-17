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
    if (!session.getAccessToken()) return;
    getApiClient()
      .me()
      .then((user) => setUserEmail(user.email))
      .catch(() => setUserEmail(null));
  }, []);

  function saveTenant() {
    const trimmed = tenantId.trim();
    if (!trimmed) {
      setError("Tenant ID is required.");
      return;
    }
    session.setTenantId(trimmed);
    setMessage("Tenant ID saved.");
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
    setMessage("Signed out.");
  }

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-semibold">Settings</h1>
      <Card title="Tenant">
        <Input label="Tenant ID" value={tenantId} onChange={(e) => setTenantId(e.target.value)} />
        <div className="mt-3 flex gap-2">
          <Button onClick={saveTenant}>Save</Button>
          <Button variant="secondary" onClick={checkApi}>Check API</Button>
        </div>
      </Card>
      <Card title="Session">
        <p className="text-sm">{userEmail ? `Signed in as ${userEmail}` : "Not signed in"}</p>
        <Button variant="secondary" className="mt-3" onClick={signOut}>Sign out</Button>
      </Card>
      {message ? <p className="text-sm text-emerald-300">{message}</p> : null}
      {error ? <p className="text-sm text-red-300">{error}</p> : null}
    </div>
  );
}
