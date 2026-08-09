"""Phase 1 foundation: auth, tenancy, RBAC, config."""

from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_super_admin_login_and_create_tenant(client: AsyncClient) -> None:
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    assert login.status_code == 200, login.text
    token = login.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert any(r["role"] == "SUPER_ADMIN" for r in me.json()["roles"])

    created = await client.post(
        "/api/v1/tenants",
        headers=headers,
        json={"name": "Acme Foods", "slug": "acme-foods", "config": {"default_currency": "INR"}},
    )
    assert created.status_code == 200, created.text
    tenant = created.json()
    assert tenant["slug"] == "acme-foods"
    assert tenant["config"]["default_currency"] == "INR"

    platform = await client.put(
        "/api/v1/platform-config/feature_flags",
        headers=headers,
        json={"value": {"otp": True, "ondc": False}},
    )
    assert platform.status_code == 200
    assert platform.json()["value"]["otp"] is True


@pytest.mark.asyncio
async def test_password_register_login_under_tenant(client: AsyncClient) -> None:
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    admin_token = admin_login.json()["access_token"]
    tenant_resp = await client.post(
        "/api/v1/tenants",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "Tenant Two", "slug": "tenant-two"},
    )
    tenant_id = tenant_resp.json()["id"]
    tenant_headers = {"X-Tenant-ID": tenant_id}

    register = await client.post(
        "/api/v1/auth/register",
        headers=tenant_headers,
        json={
            "email": "customer@example.com",
            "password": "Secret123!",
            "display_name": "Riya",
        },
    )
    assert register.status_code == 200, register.text
    assert register.json()["tenant_id"] == tenant_id

    login = await client.post(
        "/api/v1/auth/login",
        headers=tenant_headers,
        json={"email": "customer@example.com", "password": "Secret123!"},
    )
    assert login.status_code == 200
    me = await client.get(
        "/api/v1/auth/me",
        headers={
            "Authorization": f"Bearer {login.json()['access_token']}",
            "X-Tenant-ID": tenant_id,
        },
    )
    assert me.status_code == 200
    assert any(r["role"] == "CUSTOMER" for r in me.json()["roles"])


@pytest.mark.asyncio
async def test_otp_login_flow(client: AsyncClient) -> None:
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    admin_token = admin_login.json()["access_token"]
    tenant_resp = await client.post(
        "/api/v1/tenants",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "OTP Tenant", "slug": "otp-tenant"},
    )
    tenant_id = tenant_resp.json()["id"]
    headers = {"X-Tenant-ID": tenant_id}

    req = await client.post(
        "/api/v1/auth/otp/request",
        headers=headers,
        json={"phone": "+919876543210"},
    )
    assert req.status_code == 200, req.text
    code = req.json()["debug_code"]
    assert code and len(code) == 6

    verify = await client.post(
        "/api/v1/auth/otp/verify",
        headers=headers,
        json={"phone": "+919876543210", "code": code},
    )
    assert verify.status_code == 200, verify.text
    assert verify.json()["tenant_id"] == tenant_id


@pytest.mark.asyncio
async def test_customer_cannot_create_tenant(client: AsyncClient) -> None:
    admin_login = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "ChangeMe123!"},
    )
    admin_token = admin_login.json()["access_token"]
    tenant_resp = await client.post(
        "/api/v1/tenants",
        headers={"Authorization": f"Bearer {admin_token}"},
        json={"name": "RBAC Tenant", "slug": "rbac-tenant"},
    )
    tenant_id = tenant_resp.json()["id"]

    register = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={"email": "noperm@example.com", "password": "Secret123!"},
    )
    token = register.json()["access_token"]
    forbidden = await client.post(
        "/api/v1/tenants",
        headers={"Authorization": f"Bearer {token}"},
        json={"name": "Nope", "slug": "nope"},
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"


@pytest.mark.asyncio
async def test_business_config_defaults() -> None:
    from app.businesses.schemas import BusinessConfig, default_capabilities

    caps = default_capabilities("FOOD")
    assert caps["addons"] is True
    assert caps["inventory"] is False
    grocery = default_capabilities("GROCERY")
    assert grocery["inventory"] is True
    cfg = BusinessConfig(preparation_time_minutes=20)
    assert cfg.currency == "INR"
