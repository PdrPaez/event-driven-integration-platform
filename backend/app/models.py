from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def now(): return datetime.now(UTC)
class Base(DeclarativeBase): pass
class Order(Base):
    __tablename__ = "orders"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    customer_id: Mapped[str] = mapped_column(String(100)); amount_cents: Mapped[int] = mapped_column(Integer)
    currency: Mapped[str] = mapped_column(String(3)); created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
class Event(Base):
    __tablename__ = "events"
    event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100)); schema_version: Mapped[int] = mapped_column(Integer)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True)); producer: Mapped[str] = mapped_column(String(100))
    aggregate_type: Mapped[str | None] = mapped_column(String(100)); aggregate_id: Mapped[str | None] = mapped_column(String(100))
    correlation_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True)); causation_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True))
    payload: Mapped[dict] = mapped_column(JSONB); created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
class Outbox(Base):
    __tablename__ = "outbox"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True)); routing_key: Mapped[str] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="pending"); attempts: Mapped[int] = mapped_column(Integer, default=0)
    next_attempt_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now); locked_by: Mapped[str | None] = mapped_column(String(100))
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True)); published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_error_category: Mapped[str | None] = mapped_column(String(80)); last_error: Mapped[str | None] = mapped_column(Text)
class Inbox(Base):
    __tablename__ = "inbox"
    __table_args__ = (UniqueConstraint("consumer_name", "event_id"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    consumer_name: Mapped[str] = mapped_column(String(80)); event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now); result: Mapped[dict] = mapped_column(JSONB)
class Delivery(Base):
    __tablename__ = "deliveries"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True)); consumer_name: Mapped[str] = mapped_column(String(80))
    attempt: Mapped[int] = mapped_column(Integer); outcome: Mapped[str] = mapped_column(String(40)); error_category: Mapped[str | None] = mapped_column(String(80))
    trace: Mapped[dict] = mapped_column(JSONB); created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
class Destination(Base):
    __tablename__ = "destinations"
    __table_args__ = (UniqueConstraint("connector", "idempotency_key"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4); connector: Mapped[str] = mapped_column(String(80))
    idempotency_key: Mapped[str] = mapped_column(String(100)); event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True)); summary: Mapped[dict] = mapped_column(JSONB)
class DeadLetter(Base):
    __tablename__ = "dead_letters"
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4); event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True))
    connector: Mapped[str] = mapped_column(String(80)); status: Mapped[str] = mapped_column(String(30), default="open"); final_attempt: Mapped[int] = mapped_column(Integer)
    error_category: Mapped[str] = mapped_column(String(80)); error_message: Mapped[str] = mapped_column(Text); replay_count: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
class WebhookIngress(Base):
    __tablename__ = "webhook_ingress"
    __table_args__ = (UniqueConstraint("source", "external_event_id"),)
    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4); source: Mapped[str] = mapped_column(String(80)); external_event_id: Mapped[str] = mapped_column(String(150)); content_hash: Mapped[str] = mapped_column(String(64)); event_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True)); created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
class FailureMode(Base):
    __tablename__ = "failure_modes"
    connector: Mapped[str] = mapped_column(String(80), primary_key=True); mode: Mapped[str] = mapped_column(String(30), default="none")
