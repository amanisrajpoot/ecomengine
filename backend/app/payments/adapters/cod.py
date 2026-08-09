"""Cash-on-delivery payment adapter."""

from __future__ import annotations

import secrets

from app.payments.gateway import PaymentGateway
from app.payments.schemas import (
    CreatePaymentRequest,
    CreatePaymentResult,
    RefundPaymentRequest,
    RefundPaymentResult,
    VerifyPaymentRequest,
    VerifyPaymentResult,
)


class CODGateway(PaymentGateway):
    name = "cod"

    async def create_payment(self, request: CreatePaymentRequest) -> CreatePaymentResult:
        provider_ref = f"cod_{secrets.token_hex(8)}"
        return CreatePaymentResult(
            provider=self.name,
            provider_ref=provider_ref,
            # COD is authorized at checkout; capture happens on delivery (Phase 11+).
            status="AUTHORIZED",
            checkout={"method": "COD", "collect_on_delivery": True},
            raw={"amount_paise": request.amount_paise, "currency": request.currency},
        )

    async def verify_payment(self, request: VerifyPaymentRequest) -> VerifyPaymentResult:
        status = str(request.payload.get("status") or "AUTHORIZED")
        return VerifyPaymentResult(
            provider=self.name,
            provider_ref=request.provider_ref,
            status=status,
            amount_paise=request.payload.get("amount_paise"),
            raw=request.payload,
        )

    async def refund_payment(self, request: RefundPaymentRequest) -> RefundPaymentResult:
        # COD refunds are operational adjustments until settlement engine lands.
        return RefundPaymentResult(
            provider=self.name,
            provider_ref=f"cod_refund_{secrets.token_hex(6)}",
            status="REFUNDED",
            amount_paise=request.amount_paise,
            raw={"reason": request.reason, "manual": True},
        )
