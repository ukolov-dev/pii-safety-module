"""Public API schemas."""

from pydantic import BaseModel, ConfigDict, Field


class ProcessRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=False)

    payload: str
    payload_id: str = Field(min_length=1, max_length=256)


class ProcessResponse(BaseModel):
    result: str


class HealthResponse(BaseModel):
    status: str

