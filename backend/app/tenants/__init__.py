"""Tenants: multi-tenancy isolation and tenant configuration."""

from app.tenants.models import PlatformConfig, Tenant

__all__ = ["PlatformConfig", "Tenant"]
