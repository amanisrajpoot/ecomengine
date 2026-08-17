"""Phase 1: auth, tenants, RBAC."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


async def _admin_headers(client: AsyncClient) -> dict[str, str]:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    assert login.status_code == 200, login.text
    return {"Authorization": f"Bearer {login.json()['access_token']}"}


@pytest.mark.asyncio
async def test_bootstrap_super_admin_login(client: AsyncClient) -> None:
    headers = await _admin_headers(client)
    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200, me.text
    body = me.json()
    assert body["email"] == "admin@example.com"
    assert any(r["role"] == "SUPER_ADMIN" for r in body["roles"])


@pytest.mark.asyncio
async def test_super_admin_creates_tenant(client: AsyncClient) -> None:
    headers = await _admin_headers(client)
    created = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "Demo Tenant", "slug": "demo-tenant"},
    )
    assert created.status_code == 200, created.text
    tenant = created.json()
    assert tenant["slug"] == "demo-tenant"

    listed = await client.get("/api/v1/tenants", headers=headers)
    assert listed.status_code == 200
    assert any(t["id"] == tenant["id"] for t in listed.json())


@pytest.mark.asyncio
async def test_register_and_me_in_tenant(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=admin,
        json={"name": "Shop", "slug": "p1-shop"},
    )
    tenant_id = tenant.json()["id"]

    registered = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={
            "email": "customer@example.com",
            "password": "Customer123!",
            "display_name": "Customer",
        },
    )
    assert registered.status_code == 200, registered.text
    token = registered.json()["access_token"]

    me = await client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}", "X-Tenant-ID": tenant_id},
    )
    assert me.status_code == 200, me.text
    assert me.json()["email"] == "customer@example.com"
    assert any(r["role"] == "CUSTOMER" for r in me.json()["roles"])


@pytest.mark.asyncio
async def test_otp_login_flow(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=admin,
        json={"name": "OTP Shop", "slug": "p1-otp"},
    )
    tenant_id = tenant.json()["id"]
    headers = {"X-Tenant-ID": tenant_id}

    requested = await client.post(
        "/api/v1/auth/otp/request",
        headers=headers,
        json={"phone": "+919876543210"},
    )
    assert requested.status_code == 200, requested.text
    code = requested.json()["debug_code"]
    assert code

    verified = await client.post(
        "/api/v1/auth/otp/verify",
        headers=headers,
        json={"phone": "+919876543210", "code": code},
    )
    assert verified.status_code == 200, verified.text
    assert verified.json()["access_token"]


@pytest.mark.asyncio
async def test_assign_tenant_admin_role(client: AsyncClient) -> None:
    admin = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants",
        headers=admin,
        json={"name": "Admin Shop", "slug": "p1-admin"},
    )
    tenant_id = tenant.json()["id"]

    registered = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": "manager@example.com", "password": "Manager123!"},
    )
    user_id = registered.json()["user_id"]

    assign = await client.post(
        f"/api/v1/users/{user_id}/roles",
        headers=admin,
        json={"role": "TENANT_ADMIN", "tenant_id": tenant_id},
    )
    assert assign.status_code == 200, assign.status_code
    assert assign.json()["role"] == "TENANT_ADMIN"
