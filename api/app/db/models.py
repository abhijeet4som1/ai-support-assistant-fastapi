"""Database schema (SQLAlchemy 2, PostgreSQL + pgvector). The tables are created by the Alembic
migration (plain SQL under alembic/sql/); these mappings only describe them.
Timestamps and ids are generated in Python so rows inserted in one transaction stay ordered."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID, uuid4

from pgvector.sqlalchemy import Vector
from sqlalchemy import (
    BigInteger,
    Boolean,
    Computed,
    DateTime,
    Double,
    FetchedValue,
    ForeignKey,
    Integer,
    LargeBinary,
    Text,
)
from sqlalchemy.dialects.postgresql import ENUM, JSONB, TSVECTOR
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from app.schemas import Coverage, FeedbackRating, GuidelineStatus, MessageRole, MessageStatus

# Embedding dimensionality is fixed at the schema level (pgvector indexes need it).
# Must match GEMINI_EMBEDDING_DIMENSIONS; changing it requires a migration + re-ingest.
EMBEDDING_DIMENSIONS = 768


def utcnow() -> datetime:
    return datetime.now(UTC)


def _enum(enum_cls: type, name: str) -> ENUM:
    return ENUM(
        enum_cls,
        name=name,
        create_type=False,
        values_callable=lambda e: [m.value for m in e],
    )


class Base(DeclarativeBase):
    pass


def _uuid_pk() -> Mapped[UUID]:
    return mapped_column(primary_key=True, default=uuid4)


def _created_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, default=utcnow)


def _updated_at() -> Mapped[datetime]:
    return mapped_column(DateTime(timezone=True), nullable=False, default=utcnow, onupdate=utcnow)


class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = _uuid_pk()
    username: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(Text, nullable=False)
    display_name: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class RefreshToken(Base):
    """Stored hashed. `family_id` groups the chain of rotations that started at one login; reuse
    of an already-rotated token revokes the whole family (theft detection)."""

    __tablename__ = "refresh_tokens"

    id: Mapped[UUID] = _uuid_pk()
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    family_id: Mapped[UUID] = mapped_column(nullable=False)
    token_hash: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    replaced_by: Mapped[UUID | None] = mapped_column()
    created_at: Mapped[datetime] = _created_at()


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[UUID] = _uuid_pk()
    name: Mapped[str] = mapped_column(Text, nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    # Points at the guideline version used for chat; only ever a `ready` version.
    active_guideline_version_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("guideline_versions.id", ondelete="SET NULL", use_alter=True)
    )
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class GuidelineVersion(Base):
    __tablename__ = "guideline_versions"

    id: Mapped[UUID] = _uuid_pk()
    # Monotonic per-table sequence used to order versions deterministically (bigserial).
    seq: Mapped[int] = mapped_column(
        BigInteger, nullable=False, unique=True, server_default=FetchedValue()
    )
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    filename: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(Text, nullable=False)
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(Text, nullable=False)
    # Original upload, kept so the worker needs no shared volume and for re-processing.
    file_bytes: Mapped[bytes] = mapped_column(LargeBinary, nullable=False)
    raw_text: Mapped[str | None] = mapped_column(Text)
    status: Mapped[GuidelineStatus] = mapped_column(
        _enum(GuidelineStatus, "guideline_status"), nullable=False, default=GuidelineStatus.queued
    )
    chunks_total: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    chunks_embedded: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error: Mapped[str | None] = mapped_column(Text)
    job_id: Mapped[str | None] = mapped_column(Text)
    superseded_by: Mapped[UUID | None] = mapped_column()
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    ready_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class GuidelineChunk(Base):
    __tablename__ = "guideline_chunks"

    id: Mapped[UUID] = _uuid_pk()
    version_id: Mapped[UUID] = mapped_column(
        ForeignKey("guideline_versions.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    token_count: Mapped[int] = mapped_column(Integer, nullable=False)
    # NULL until the worker has embedded the chunk (makes ingestion resumable).
    embedding: Mapped[Any | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS))
    # Full-text index of title + content (English stemming), maintained by Postgres. Used by the
    # keyword rescue in retrieval.
    search_vector: Mapped[Any | None] = mapped_column(
        TSVECTOR,
        Computed("to_tsvector('english', coalesce(title, '') || ' ' || content)", persisted=True),
    )


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[UUID] = _uuid_pk()
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(Text, nullable=False, default="")
    # Rolling summary of messages that no longer fit the history window, and the last message it covers.
    history_summary: Mapped[str | None] = mapped_column(Text)
    history_summary_upto: Mapped[UUID | None] = mapped_column()
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    last_message_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, default=utcnow
    )
    # Coverage of the latest assistant answer, denormalised so the history filter is an indexed equality.
    last_coverage: Mapped[Coverage | None] = mapped_column(_enum(Coverage, "coverage"))
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[UUID] = _uuid_pk()
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    role: Mapped[MessageRole] = mapped_column(_enum(MessageRole, "message_role"), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[MessageStatus] = mapped_column(
        _enum(MessageStatus, "message_status"), nullable=False, default=MessageStatus.ok
    )
    error: Mapped[str | None] = mapped_column(Text)
    # Structured assistant output (AssistantGuidance) for assistant messages.
    guidance: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    coverage: Mapped[Coverage | None] = mapped_column(_enum(Coverage, "coverage"))
    retrieval: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    corrections_used: Mapped[list[dict[str, Any]] | None] = mapped_column(JSONB)
    guideline_version_id: Mapped[UUID | None] = mapped_column()
    model: Mapped[str | None] = mapped_column(Text)
    prompt_tokens: Mapped[int | None] = mapped_column(Integer)
    # Visible answer tokens; thinking tokens are reported separately by the provider.
    completion_tokens: Mapped[int | None] = mapped_column(Integer)
    thinking_tokens: Mapped[int | None] = mapped_column(Integer)
    # Provider-reported total for the call (prompt + thinking + answer).
    total_tokens: Mapped[int | None] = mapped_column(Integer)
    latency_ms: Mapped[int | None] = mapped_column(Integer)
    # Observability trace id (Langfuse) of the turn that produced this answer; feedback scores attach to it.
    trace_id: Mapped[str | None] = mapped_column(Text)
    created_by: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = _created_at()


class Feedback(Base):
    __tablename__ = "feedback"

    id: Mapped[UUID] = _uuid_pk()
    message_id: Mapped[UUID] = mapped_column(
        ForeignKey("messages.id", ondelete="CASCADE"), nullable=False
    )
    conversation_id: Mapped[UUID] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
    )
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("companies.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[UUID] = mapped_column(ForeignKey("users.id"), nullable=False)
    rating: Mapped[FeedbackRating] = mapped_column(
        _enum(FeedbackRating, "feedback_rating"), nullable=False
    )
    what_was_wrong: Mapped[str | None] = mapped_column(Text)
    corrected_answer: Mapped[str | None] = mapped_column(Text)
    # The customer message that led to the rated answer; embedded for similarity retrieval.
    query_text: Mapped[str] = mapped_column(Text, nullable=False)
    query_embedding: Mapped[Any | None] = mapped_column(Vector(EMBEDDING_DIMENSIONS))
    guideline_version_id: Mapped[UUID] = mapped_column(nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    score: Mapped[float | None] = mapped_column(Double)
    created_at: Mapped[datetime] = _created_at()
    updated_at: Mapped[datetime] = _updated_at()
