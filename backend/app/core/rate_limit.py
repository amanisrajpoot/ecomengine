"""Redis-backed rate limiting with in-memory fallback."""

from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import Request

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.metrics import metrics_store

_EXEMPT_PREFIXES = ("/health", "/metrics")


class _MemoryLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def allow(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.monotonic()
        bucket = self._hits[key]
        while bucket and now - bucket[0] > window_seconds:
            bucket.popleft()
        if len(bucket) >= limit:
            return False
        bucket.append(now)
        return True


_memory_limiter = _MemoryLimiter()


def clear_memory_rate_limits() -> None:
    _memory_limiter._hits.clear()


def _client_key(request: Request) -> str:
    tenant = request.headers.get("X-Tenant-ID", "")
    client_host = request.client.host if request.client else "unknown"
    return f"{client_host}:{tenant}"


def _is_exempt(path: str) -> bool:
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in _EXEMPT_PREFIXES)


async def _allow_redis(key: str, limit: int, window_seconds: int) -> bool | None:
    try:
        from app.core.redis import get_redis

        redis = get_redis()
        bucket_key = f"rate:{key}"
        count = await redis.incr(bucket_key)
        if count == 1:
            await redis.expire(bucket_key, window_seconds)
        return count <= limit
    except Exception:
        return None


async def enforce_rate_limit(request: Request) -> None:
    settings = get_settings()
    if not settings.rate_limit_enabled or _is_exempt(request.url.path):
        return

    limit = settings.rate_limit_per_minute
    window = settings.rate_limit_window_seconds
    key = _client_key(request)

    allowed = await _allow_redis(key, limit, window)
    if allowed is None:
        allowed = _memory_limiter.allow(key, limit, window)

    if not allowed:
        metrics_store.record_rate_limited()
        raise AppError(
            "RATE_LIMITED",
            "Too many requests. Please retry shortly.",
            status_code=429,
            details={"limit_per_window": limit, "window_seconds": window},
        )
