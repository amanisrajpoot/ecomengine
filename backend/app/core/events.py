"""In-process domain event bus (no Kafka/RabbitMQ in V1)."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Awaitable, Callable
from typing import Any

EventHandler = Callable[[str, dict[str, Any]], Awaitable[None] | None]


class EventBus:
    """Simple publish/subscribe bus for domain events."""

    def __init__(self) -> None:
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: EventHandler) -> None:
        self._handlers[event_name].append(handler)

    async def publish(self, event_name: str, payload: dict[str, Any] | None = None) -> None:
        data = payload or {}
        for handler in self._handlers.get(event_name, []):
            result = handler(event_name, data)
            if hasattr(result, "__await__"):
                await result  # type: ignore[misc]


event_bus = EventBus()
