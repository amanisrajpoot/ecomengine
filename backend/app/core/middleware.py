"""HTTP middleware for request IDs, timing, and metrics."""

from __future__ import annotations

import logging
import time
import uuid

from fastapi import Request, Response
from fastapi.responses import JSONResponse

from app.core.errors import AppError
from app.core.metrics import metrics_store
from app.core.rate_limit import enforce_rate_limit

logger = logging.getLogger("commerce.http")


def _error_response(exc: AppError, request_id: str, elapsed_ms: int) -> JSONResponse:
    metrics_store.record_request(exc.status_code)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
        headers={
            "X-Request-ID": request_id,
            "X-Response-Time-Ms": str(elapsed_ms),
        },
    )


async def observability_middleware(request: Request, call_next) -> Response:
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    start = time.perf_counter()

    try:
        await enforce_rate_limit(request)
    except AppError as exc:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        return _error_response(exc, request_id, elapsed_ms)

    try:
        response = await call_next(request)
    except Exception:
        elapsed_ms = int((time.perf_counter() - start) * 1000)
        logger.exception(
            "request_failed id=%s method=%s path=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            elapsed_ms,
        )
        raise

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    metrics_store.record_request(response.status_code)
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-Ms"] = str(elapsed_ms)

    if request.url.path not in ("/health", "/metrics"):
        logger.info(
            "request id=%s method=%s path=%s status=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
        )

    return response
