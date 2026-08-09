"""Fulfillment: order fulfillment records decoupled from logistics."""

from app.fulfillment.models import Fulfillment, FulfillmentStatusEvent

__all__ = ["Fulfillment", "FulfillmentStatusEvent"]
