"""Phase 38: business staff list/assign API for merchant staff UI."""

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


async def _business_setup(client: AsyncClient, slug: str) -> tuple[dict[str, str], str]:
    headers = await _admin_headers(client)
    tenant = await client.post(
        "/api/v1/tenants", headers=headers, json={"name": slug, "slug": slug}
    )
    headers["X-Tenant-ID"] = tenant.json()["id"]
    biz = await client.post(
        "/api/v1/businesses",
        headers=headers,
        json={"name": f"{slug}-store", "type": "FOOD", "status": "ACTIVE"},
    )
    return headers, biz.json()["id"]


@pytest.mark.asyncio
async def test_owner_lists_and_assigns_staff_by_email(client: AsyncClient) -> None:
    admin, business_id = await _business_setup(client, "p38-staff")
    tenant_id = admin["X-Tenant-ID"]

    owner_reg = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={
            "email": "owner-p38@example.com",
            "password": "Owner123!",
            "display_name": "Owner",
        },
    )
    assert owner_reg.status_code == 200, owner_reg.text
    owner_user_id = owner_reg.json()["user_id"]

    owner_bind = await client.post(
        f"/api/v1/users/{owner_user_id}/roles",
        headers=admin,
        json={
            "role": "BUSINESS_OWNER",
            "tenant_id": tenant_id,
            "business_id": business_id,
        },
    )
    assert owner_bind.status_code == 200, owner_bind.text

    owner_headers = {
        "Authorization": f"Bearer {owner_reg.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }

    staff_reg = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={
            "email": "staff-p38@example.com",
            "password": "Staff123!",
            "display_name": "Counter Staff",
        },
    )
    assert staff_reg.status_code == 200, staff_reg.text

    assign = await client.post(
        f"/api/v1/businesses/{business_id}/staff",
        headers=owner_headers,
        json={"email": "staff-p38@example.com", "role": "STAFF"},
    )
    assert assign.status_code == 200, assign.text
    body = assign.json()
    assert body["role"] == "STAFF"
    assert body["email"] == "staff-p38@example.com"
    assert body["display_name"] == "Counter Staff"

    listed = await client.get(
        f"/api/v1/businesses/{business_id}/staff",
        headers=owner_headers,
    )
    assert listed.status_code == 200, listed.text
    roles = {row["email"]: row["role"] for row in listed.json()}
    assert roles["staff-p38@example.com"] == "STAFF"
    assert "owner-p38@example.com" in roles
    assert roles["owner-p38@example.com"] == "BUSINESS_OWNER"


@pytest.mark.asyncio
async def test_manager_can_list_staff_but_not_assign(client: AsyncClient) -> None:
    admin, business_id = await _business_setup(client, "p38-manager")
    tenant_id = admin["X-Tenant-ID"]

    manager_reg = await client.post(
        "/api/v1/auth/register",
        headers={"X-Tenant-ID": tenant_id},
        json={
            "email": "manager-p38@example.com",
            "password": "Manager123!",
            "display_name": "Manager",
        },
    )
    assert manager_reg.status_code == 200, manager_reg.text
    manager_user_id = manager_reg.json()["user_id"]

    bind = await client.post(
        f"/api/v1/users/{manager_user_id}/roles",
        headers=admin,
        json={
            "role": "BUSINESS_MANAGER",
            "tenant_id": tenant_id,
            "business_id": business_id,
        },
    )
    assert bind.status_code == 200, bind.text

    manager_headers = {
        "Authorization": f"Bearer {manager_reg.json()['access_token']}",
        "X-Tenant-ID": tenant_id,
    }

    listed = await client.get(
        f"/api/v1/businesses/{business_id}/staff",
        headers=manager_headers,
    )
    assert listed.status_code == 200, listed.text

    denied = await client.post(
        f"/api/v1/businesses/{business_id}/staff",
        headers=manager_headers,
        json={"email": "manager-p38@example.com", "role": "STAFF"},
    )
    assert denied.status_code == 403, denied.text
