"""Payment gateway registry — multi-provider support."""

from __future__ import annotations

from app.core.errors import AppError
from app.payments.adapters.cashfree import CashfreeGateway
from app.payments.adapters.cod import CODGateway
from app.payments.gateway import PaymentGateway


class GatewayRegistry:
    def __init__(self) -> None:
        self._gateways: dict[str, PaymentGateway] = {}

    def register(self, gateway: PaymentGateway) -> None:
        self._gateways[gateway.name] = gateway

    def get(self, name: str) -> PaymentGateway:
        gateway = self._gateways.get(name)
        if not gateway:
            raise AppError(
                "PAYMENT_PROVIDER_UNSUPPORTED",
                f"Payment provider '{name}' is not registered",
                status_code=400,
                details={"available": sorted(self._gateways.keys())},
            )
        return gateway

    def list_providers(self) -> list[str]:
        return sorted(self._gateways.keys())


def build_default_registry() -> GatewayRegistry:
    registry = GatewayRegistry()
    registry.register(CashfreeGateway())
    registry.register(CODGateway())
    # Razorpay / UPI / others: register additional adapters here when credentials exist.
    return registry


gateway_registry = build_default_registry()
