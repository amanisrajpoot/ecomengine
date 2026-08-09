"""Businesses: onboarding, types, and capability configuration."""

from app.businesses.models import Business
from app.businesses.schemas import BusinessConfig, default_capabilities

__all__ = ["Business", "BusinessConfig", "default_capabilities"]
