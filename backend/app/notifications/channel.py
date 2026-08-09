"""Abstract notification channel interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class SendNotificationRequest:
    recipient: str
    subject: str | None
    body: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SendNotificationResult:
    provider: str
    provider_ref: str
    status: str
    raw: dict[str, Any] = field(default_factory=dict)


class NotificationChannel(ABC):
    name: str

    @abstractmethod
    async def send(self, request: SendNotificationRequest) -> SendNotificationResult:
        raise NotImplementedError
