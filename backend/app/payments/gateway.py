"""Abstract payment gateway interface — all providers implement this."""

from __future__ import annotations

from abc import ABC, abstractmethod

from app.payments.schemas import (
    CreatePaymentRequest,
    CreatePaymentResult,
    RefundPaymentRequest,
    RefundPaymentResult,
    VerifyPaymentRequest,
    VerifyPaymentResult,
)


class PaymentGateway(ABC):
    """Provider adapter contract.

    New gateways (Razorpay, UPI collect, etc.) register beside Cashfree/COD
    without changing order/payment orchestration.
    """

    name: str

    @abstractmethod
    async def create_payment(self, request: CreatePaymentRequest) -> CreatePaymentResult:
        raise NotImplementedError

    @abstractmethod
    async def verify_payment(self, request: VerifyPaymentRequest) -> VerifyPaymentResult:
        raise NotImplementedError

    async def capture_payment(self, provider_ref: str) -> VerifyPaymentResult:
        """Optional explicit capture; default = verify current status."""
        return await self.verify_payment(VerifyPaymentRequest(provider_ref=provider_ref))

    @abstractmethod
    async def refund_payment(self, request: RefundPaymentRequest) -> RefundPaymentResult:
        raise NotImplementedError
