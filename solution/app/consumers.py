"""Validated consumer policies and authentication; secrets stay in environment."""

from __future__ import annotations

import hmac
import os
from pathlib import Path

import yaml  # type: ignore[import-untyped]
from fastapi import HTTPException
from pydantic import BaseModel, ConfigDict, Field, model_validator


class ConsumerPolicy(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)
    enabled: bool = True
    public_access: bool = False
    api_key_env: str | None = None
    mask_types: frozenset[str] | None = None
    demask_enabled: bool = True
    vault_ttl_seconds: int = Field(default=900, ge=30, le=86400)

    @model_validator(mode="after")
    def require_credentials(self) -> ConsumerPolicy:
        if self.enabled and not self.public_access and not self.api_key_env:
            raise ValueError("enabled private consumers require api_key_env")
        return self


class ConsumerConfig(BaseModel):
    model_config = ConfigDict(extra="forbid")
    default_consumer: str = "portal"
    consumers: dict[str, ConsumerPolicy]


def load_consumers(path: str) -> ConsumerConfig:
    config = ConsumerConfig.model_validate(yaml.safe_load(Path(path).read_text()))
    if config.default_consumer not in config.consumers:
        raise ValueError("default consumer must be configured")
    for name, policy in config.consumers.items():
        if not name or len(name) > 64 or not all(c.isalnum() or c in "_-" for c in name):
            raise ValueError("consumer names must be short identifiers")
        if policy.enabled and not policy.public_access:
            if len(os.environ.get(policy.api_key_env or "", "")) < 32:
                raise ValueError(f"consumer {name}: credential must have at least 32 characters")
    return config


def authenticate(
    config: ConsumerConfig, consumer_id: str | None, api_key: str | None
) -> tuple[str, ConsumerPolicy]:
    name = consumer_id if consumer_id is not None else config.default_consumer
    policy = config.consumers.get(name)
    if policy is None or not policy.enabled:
        raise HTTPException(403, "consumer is not allowed")
    if not policy.public_access:
        expected = os.environ.get(policy.api_key_env or "", "")
        if not expected or not hmac.compare_digest((api_key or "").encode(), expected.encode()):
            raise HTTPException(401, "invalid consumer credentials")
    return name, policy
