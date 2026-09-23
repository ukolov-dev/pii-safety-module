"""Application settings loaded exclusively from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    redis_url: str | None = None
    mapping_encryption_key: str | None = None
    mapping_encryption_key_file: str | None = None
    mapping_ttl_seconds: int = Field(default=900, ge=30, le=86400)
    process_api_key: str | None = Field(default=None, min_length=16)
    max_payload_chars: int = Field(default=2_000_000, ge=1_000, le=10_000_000)
    max_request_body_bytes: int = Field(
        default=8 * 1024 * 1024,
        ge=16 * 1024,
        le=32 * 1024 * 1024,
    )


settings = Settings()
