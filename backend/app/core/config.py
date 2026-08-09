"""Application settings loaded from environment."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "commerce-engine"
    app_version: str = "0.6.0"
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


@lru_cache
def get_settings() -> Settings:
    return Settings()
