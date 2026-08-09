"""Beckn / ONDC protocol envelopes (subset used by this adapter)."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from pydantic import BaseModel, Field


class BecknContext(BaseModel):
    domain: str = "ONDC:RET10"
    country: str = "IND"
    city: str = "std:080"
    action: str
    core_version: str = "1.2.0"
    bap_id: str
    bap_uri: str
    bpp_id: str
    bpp_uri: str
    transaction_id: str
    message_id: str
    timestamp: str
    ttl: str = "PT30S"


class BecknRequest(BaseModel):
    context: BecknContext
    message: dict[str, Any] = Field(default_factory=dict)


class BecknResponse(BaseModel):
    context: BecknContext
    message: dict[str, Any] = Field(default_factory=dict)


class OndcMetaRead(BaseModel):
    adapter: str = "commerce-engine-ondc"
    mock_mode: bool
    supported_domains: list[str]
    supported_actions: list[str]
    version: str
