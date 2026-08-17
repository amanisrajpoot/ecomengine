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

    jwt_secret: str = "dev-change-me-in-production"
    jwt_algorithm: str = "HS256"
    jwt_ttl_seconds: int = 86400 * 7

    otp_ttl_seconds: int = 300
    otp_echo_in_response: bool = True

    bootstrap_super_admin_email: str = "admin@example.com"
    bootstrap_super_admin_password: str = "ChangeMe123!"

    s3_endpoint_url: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "commerce"
    s3_region: str = "us-east-1"


@lru_cache
def get_settings() -> Settings:
    return Settings()
