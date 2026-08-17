"""Payment gateway interface and providers."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Protocol


class PaymentProvider(StrEnum):
    COD = "COD"
    RAZORPAY = "RAZORPAY"


class PaymentStatus(StrEnum):
    CREATED = "CREATED"
    PENDING = "PENDING"
    CAPTURED = "CAPTURED"
    FAILED = "FAILED"
    REFUNDED = "REFUNDED"


@dataclass
class GatewayInitResult:
    status: PaymentStatus
    provider_ref: str | None = None
    client_payload: dict | None = None


class PaymentGateway(Protocol):
    provider: PaymentProvider

    async def initiate(self, *, amount_paise: int, currency: str, order_id: str) -> GatewayInitResult:
        ...

    async def capture(self, *, provider_ref: str | None, amount_paise: int) -> PaymentStatus:
        ...


class CodGateway:
    provider = PaymentProvider.COD

    async def initiate(
        self, *, amount_paise: int, currency: str, order_id: str
    ) -> GatewayInitResult:
        _ = amount_paise, currency, order_id
        return GatewayInitResult(status=PaymentStatus.PENDING, provider_ref=f"cod-{order_id}")

    async def capture(self, *, provider_ref: str | None, amount_paise: int) -> PaymentStatus:
        _ = provider_ref, amount_paise
        return PaymentStatus.CAPTURED


class RazorpayGateway:
    """Stub gateway — returns client payload for future Razorpay integration."""

    provider = PaymentProvider.RAZORPAY

    async def initiate(
        self, *, amount_paise: int, currency: str, order_id: str
    ) -> GatewayInitResult:
        ref = f"rzp_stub_{order_id[:8]}"
        return GatewayInitResult(
            status=PaymentStatus.PENDING,
            provider_ref=ref,
            client_payload={
                "provider": "RAZORPAY",
                "order_id": order_id,
                "amount_paise": amount_paise,
                "currency": currency,
                "razorpay_order_id": ref,
                "key_id": "rzp_test_stub",
            },
        )

    async def capture(self, *, provider_ref: str | None, amount_paise: int) -> PaymentStatus:
        _ = provider_ref, amount_paise
        return PaymentStatus.CAPTURED


def get_gateway(provider: str) -> PaymentGateway:
    if provider == PaymentProvider.COD.value:
        return CodGateway()
    if provider == PaymentProvider.RAZORPAY.value:
        return RazorpayGateway()
    raise ValueError(f"Unknown payment provider: {provider}")
