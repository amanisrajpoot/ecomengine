"""Notification channel registry."""

from __future__ import annotations

from app.core.errors import AppError
from app.notifications.adapters.sms_mock import MockSmsChannel
from app.notifications.channel import NotificationChannel


class ChannelRegistry:
    def __init__(self) -> None:
        self._channels: dict[str, NotificationChannel] = {}

    def register(self, channel: NotificationChannel) -> None:
        self._channels[channel.name] = channel

    def get(self, name: str) -> NotificationChannel:
        channel = self._channels.get(name)
        if not channel:
            raise AppError(
                "NOTIFICATION_CHANNEL_UNSUPPORTED",
                f"Channel '{name}' is not registered",
                status_code=400,
                details={"available": sorted(self._channels.keys())},
            )
        return channel


def build_default_registry() -> ChannelRegistry:
    registry = ChannelRegistry()
    registry.register(MockSmsChannel())
    return registry


channel_registry = build_default_registry()
