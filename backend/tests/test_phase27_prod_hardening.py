"""Phase 27: production hardening — rate limits and observability."""

from __future__ import annotations

import os

import pytest
from httpx import AsyncClient

from app.core.config import get_settings
from app.core.rate_limit import clear_memory_rate_limits


@pytest.fixture
def rate_limit_enabled() -> None:
    os.environ["RATE_LIMIT_ENABLED"] = "true"
    os.environ["RATE_LIMIT_PER_MINUTE"] = "5"
    os.environ["RATE_LIMIT_WINDOW_SECONDS"] = "60"
    get_settings.cache_clear()
    clear_memory_rate_limits()
    yield
    os.environ.pop("RATE_LIMIT_ENABLED", None)
    os.environ.pop("RATE_LIMIT_PER_MINUTE", None)
    get_settings.cache_clear()
    clear_memory_rate_limits()


@pytest.mark.asyncio
async def test_health_includes_version(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert body["version"] == get_settings().app_version
    assert "environment" in body


@pytest.mark.asyncio
async def test_metrics_prometheus_format(client: AsyncClient) -> None:
    await client.get("/health")
    metrics = await client.get("/metrics")
    assert metrics.status_code == 200
    text = metrics.text
    assert "commerce_requests_total" in text
    assert "commerce_http_responses_total" in text


@pytest.mark.asyncio
async def test_request_observability_headers(client: AsyncClient) -> None:
    response = await client.get("/api/v1/meta", headers={"X-Request-ID": "trace-123"})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == "trace-123"
    assert response.headers.get("X-Response-Time-Ms") is not None


@pytest.mark.asyncio
async def test_rate_limit_returns_429(client: AsyncClient, rate_limit_enabled: None) -> None:
    for _ in range(5):
        ok = await client.get("/api/v1/meta")
        assert ok.status_code == 200

    limited = await client.get("/api/v1/meta")
    assert limited.status_code == 429
    body = limited.json()
    assert body["error"]["code"] == "RATE_LIMITED"
    assert limited.headers.get("X-Request-ID")

    exempt = await client.get("/health")
    assert exempt.status_code == 200
