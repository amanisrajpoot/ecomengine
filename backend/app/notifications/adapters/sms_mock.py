"""Mock SMS adapter — records sends without external provider."""

from __future__ import annotations

import secrets

from app.notifications.channel import NotificationChannel, SendNotificationRequest, SendNotificationResult


class MockSmsChannel(NotificationChannel):
    name = "sms_mock"

    async def send(self, request: SendNotificationRequest) -> SendNotificationResult:
        provider_ref = f"sms_mock_{secrets.token_hex(6)}"
        return SendNotificationResult(
            provider=self.name,
            provider_ref=provider_ref,
            status="SENT",
            raw={
                "to": request.recipient,
                "body": request.body,
                "mock": True,
            },
        )
