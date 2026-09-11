from datetime import UTC, datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field


class CanonicalEvent(BaseModel):
    model_config = ConfigDict(extra="forbid")
    event_id: UUID = Field(default_factory=uuid4); event_type: str; schema_version: int
    occurred_at: datetime = Field(default_factory=lambda: datetime.now(UTC)); producer: str
    aggregate_type: str | None = None; aggregate_id: str | None = None; correlation_id: UUID = Field(default_factory=uuid4); causation_id: UUID | None = None
    payload: dict
