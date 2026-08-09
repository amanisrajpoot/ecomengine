"""Cashfree Payments gateway adapter (Orders API v3)."""

from __future__ import annotations

import secrets
from typing import Any

import httpx

from app.core.config import get_settings
from app.core.errors import AppError
from app.payments.gateway import PaymentGateway
from app.payments.schemas import (
    CreatePaymentRequest,
    CreatePaymentResult,
    RefundPaymentRequest,
    RefundPaymentResult,
    VerifyPaymentRequest,
    VerifyPaymentResult,
)


class CashfreeGateway(PaymentGateway):
    name = "cashfree"

    def __init__(self) -> None:
        settings = get_settings()
        self.client_id = settings.cashfree_client_id
        self.client_secret = settings.cashfree_client_secret
        self.api_version = settings.cashfree_api_version
        self.mock = settings.payments_mock or not (self.client_id and self.client_secret)
        env = settings.cashfree_env.lower()
        self.base_url = (
            "https://api.cashfree.com/pg"
            if env == "production"
            else "https://sandbox.cashfree.com/pg"
        )

    def _headers(self, idempotency_key: str | None = None) -> dict[str, str]:
        headers = {
            "x-client-id": self.client_id or "",
            "x-client-secret": self.client_secret or "",
            "x-api-version": self.api_version,
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if idempotency_key:
            headers["x-idempotency-key"] = idempotency_key
        return headers

    async def create_payment(self, request: CreatePaymentRequest) -> CreatePaymentResult:
        if self.mock:
            provider_ref = f"cf_mock_{secrets.token_hex(8)}"
            session_id = f"session_{secrets.token_hex(8)}"
            return CreatePaymentResult(
                provider=self.name,
                provider_ref=provider_ref,
                status="PENDING",
                checkout={
                    "payment_session_id": session_id,
                    "order_id": provider_ref,
                    "mode": "mock",
                    "environment": "sandbox",
                },
                raw={"mock": True, "order_amount": request.amount_paise / 100},
            )

        # Cashfree expects rupees (float), we store paise.
        amount_rupees = round(request.amount_paise / 100, 2)
        body: dict[str, Any] = {
            "order_id": request.idempotency_key or request.order_id.replace("-", "")[:40],
            "order_amount": amount_rupees,
            "order_currency": request.currency,
            "customer_details": {
                "customer_id": request.customer_id[:50],
                "customer_phone": request.customer_phone or "9999999999",
            },
            "order_meta": {},
        }
        if request.customer_email:
            body["customer_details"]["customer_email"] = request.customer_email
        if request.return_url:
            body["order_meta"]["return_url"] = request.return_url
        if request.notify_url:
            body["order_meta"]["notify_url"] = request.notify_url

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/orders",
                headers=self._headers(request.idempotency_key),
                json=body,
            )
        if response.status_code >= 400:
            raise AppError(
                "CASHFREE_CREATE_FAILED",
                "Cashfree create order failed",
                status_code=502,
                details={"status_code": response.status_code, "body": _safe_json(response)},
            )
        data = response.json()
        provider_ref = str(data.get("order_id") or body["order_id"])
        return CreatePaymentResult(
            provider=self.name,
            provider_ref=provider_ref,
            status="PENDING",
            checkout={
                "payment_session_id": data.get("payment_session_id"),
                "order_id": provider_ref,
                "payment_url": data.get("payment_link"),
                "environment": get_settings().cashfree_env,
            },
            raw=data,
        )

    async def verify_payment(self, request: VerifyPaymentRequest) -> VerifyPaymentResult:
        # Webhook / client can pass explicit status for mock verification.
        if self.mock or request.payload.get("mock_status"):
            status = str(request.payload.get("mock_status") or request.payload.get("status") or "CAPTURED")
            amount = request.payload.get("amount_paise")
            return VerifyPaymentResult(
                provider=self.name,
                provider_ref=request.provider_ref,
                status=status,
                amount_paise=int(amount) if amount is not None else None,
                raw={"mock": True, **request.payload},
            )

        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{self.base_url}/orders/{request.provider_ref}",
                headers=self._headers(),
            )
        if response.status_code >= 400:
            raise AppError(
                "CASHFREE_VERIFY_FAILED",
                "Cashfree order fetch failed",
                status_code=502,
                details={"status_code": response.status_code, "body": _safe_json(response)},
            )
        data = response.json()
        cf_status = str(data.get("order_status") or "").upper()
        mapped = {
            "ACTIVE": "PENDING",
            "PAID": "CAPTURED",
            "EXPIRED": "FAILED",
            "CANCELLED": "CANCELLED",
        }.get(cf_status, "PENDING")
        amount_paise = None
        if data.get("order_amount") is not None:
            amount_paise = int(round(float(data["order_amount"]) * 100))
        return VerifyPaymentResult(
            provider=self.name,
            provider_ref=request.provider_ref,
            status=mapped,
            amount_paise=amount_paise,
            raw=data,
        )

    async def refund_payment(self, request: RefundPaymentRequest) -> RefundPaymentResult:
        if self.mock:
            return RefundPaymentResult(
                provider=self.name,
                provider_ref=f"cf_refund_mock_{secrets.token_hex(6)}",
                status="REFUNDED",
                amount_paise=request.amount_paise,
                raw={"mock": True, "reason": request.reason},
            )

        body = {
            "refund_amount": round(request.amount_paise / 100, 2),
            "refund_id": request.idempotency_key or f"refund_{secrets.token_hex(6)}",
            "refund_note": request.reason or "refund",
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{self.base_url}/orders/{request.provider_ref}/refunds",
                headers=self._headers(request.idempotency_key),
                json=body,
            )
        if response.status_code >= 400:
            raise AppError(
                "CASHFREE_REFUND_FAILED",
                "Cashfree refund failed",
                status_code=502,
                details={"status_code": response.status_code, "body": _safe_json(response)},
            )
        data = response.json()
        return RefundPaymentResult(
            provider=self.name,
            provider_ref=str(data.get("refund_id") or body["refund_id"]),
            status="REFUNDED" if str(data.get("refund_status", "")).upper() in {"SUCCESS", "PENDING", ""} else "FAILED",
            amount_paise=request.amount_paise,
            raw=data,
        )


def _safe_json(response: httpx.Response) -> Any:
    try:
        return response.json()
    except Exception:  # noqa: BLE001
        return {"text": response.text[:500]}
