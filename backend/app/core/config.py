"""Application settings loaded from environment."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "commerce-engine"
    app_version: str = "0.34.0"
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://commerce:commerce@localhost:5432/commerce"
    redis_url: str = "redis://localhost:6379/0"

    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "commerce"
    s3_region: str = "us-east-1"

    jwt_secret: str = "dev-only-change-me-commerce-engine-jwt-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24

    otp_length: int = 6
    otp_ttl_seconds: int = 300
    # In development, OTP codes are returned in API responses for testing.
    otp_echo_in_response: bool = True

    # Payments — multi-gateway
    payments_default_provider: str = "cashfree"
    # When true (or credentials missing), Cashfree adapter runs in mock mode.
    payments_mock: bool = True
    cashfree_client_id: str = ""
    cashfree_client_secret: str = ""
    cashfree_env: str = "sandbox"  # sandbox | production
    cashfree_api_version: str = "2023-08-01"

    # Ledger — default merchant commission (10%) when tenant config omits commission_bps.
    ledger_default_commission_bps: int = 1000

    # ONDC adapter — mock mode skips subscriber auth and records callbacks locally.
    ondc_mock: bool = True
    ondc_send_callbacks: bool = False

    # Notifications — default SMS channel (mock in dev).
    notifications_default_channel: str = "sms_mock"

    # CORS — comma-separated origins for browser PWAs (different ports than API).
    cors_origins: str = (
        "http://localhost:3000,http://localhost:3001,http://localhost:3002,"
        "http://localhost:3003,http://127.0.0.1:3000,http://127.0.0.1:3001,"
        "http://127.0.0.1:3002,http://127.0.0.1:3003"
    )


def cors_origin_list(settings: Settings | None = None) -> list[str]:
    s = settings or get_settings()
    return [origin.strip() for origin in s.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
