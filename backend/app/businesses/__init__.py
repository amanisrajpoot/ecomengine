"""Businesses: onboarding, types, and capability configuration."""

from app.businesses.models import Business
from app.businesses.schemas import BusinessConfig, BusinessType, default_capabilities

__all__ = ["Business", "BusinessConfig", "BusinessType", "default_capabilities"]
