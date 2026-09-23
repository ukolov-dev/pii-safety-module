"""Application settings loaded exclusively from environment variables."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="", case_sensitive=False)

    redis_url: str | None = None
    mapping_encryption_key: str | None = None
    mapping_ttl_seconds: int = Field(default=900, ge=30, le=86400)
    max_payload_chars: int = Field(default=2_000_000, ge=1_000, le=10_000_000)


settings = Settings()

