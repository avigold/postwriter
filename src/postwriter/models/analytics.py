"""Analytics models: DeviceInstance, ValidationResultRecord, RepairAction, ScoreVector."""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import Boolean, DateTime, Enum, Float, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from postwriter.models.base import Base, UUIDMixin
from postwriter.types import RepairPriority, RepairStatus


class DeviceInstance(UUIDMixin, Base):
    __tablename__ = "device_instances"

    manuscript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manuscripts.id", ondelete="CASCADE")
    )
    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE")
    )
    draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scene_drafts.id", ondelete="CASCADE")
    )
    device_type: Mapped[str] = mapped_column(String(100))
    subtype: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    span_start: Mapped[int] = mapped_column(Integer)
    span_end: Mapped[int] = mapped_column(Integer)
    estimated_function: Mapped[str] = mapped_column(String(200), default="")
    speaker_character_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("characters.id", ondelete="SET NULL"), nullable=True
    )
    imagery_domain: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    intensity: Mapped[float] = mapped_column(Float, default=0.5)
    confidence: Mapped[float] = mapped_column(Float, default=0.8)
    novelty_score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    intentional: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ValidationResultRecord(UUIDMixin, Base):
    __tablename__ = "validation_results"

    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE")
    )
    draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scene_drafts.id", ondelete="CASCADE")
    )
    validator_type: Mapped[str] = mapped_column(String(100))
    is_hard: Mapped[bool] = mapped_column(Boolean)
    passed: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    score: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    diagnosis: Mapped[str] = mapped_column(Text, default="")
    evidence: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    span_references: Mapped[list[Any]] = mapped_column(JSONB, default=list)
    confidence: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class RepairAction(UUIDMixin, Base):
    __tablename__ = "repair_actions"

    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE")
    )
    draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scene_drafts.id", ondelete="CASCADE")
    )
    priority: Mapped[int] = mapped_column(Integer)
    target_dimension: Mapped[str] = mapped_column(String(200))
    target_span: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    issue_reference_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("validation_results.id", ondelete="SET NULL"),
        nullable=True,
    )
    instruction: Mapped[str] = mapped_column(Text, default="")
    preserve_constraints: Mapped[list[str]] = mapped_column(JSONB, default=list)
    allowed_interventions: Mapped[list[str]] = mapped_column(JSONB, default=list)
    banned_interventions: Mapped[list[str]] = mapped_column(JSONB, default=list)
    status: Mapped[RepairStatus] = mapped_column(
        Enum(RepairStatus, native_enum=False), default=RepairStatus.PLANNED
    )
    result_draft_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scene_drafts.id", ondelete="SET NULL"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )


class ScoreVector(UUIDMixin, Base):
    __tablename__ = "score_vectors"

    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE")
    )
    draft_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scene_drafts.id", ondelete="CASCADE")
    )

    # Soft critic dimensions
    tension: Mapped[float] = mapped_column(Float, default=0.5)
    emotional_credibility: Mapped[float] = mapped_column(Float, default=0.5)
    prose_vitality: Mapped[float] = mapped_column(Float, default=0.5)
    voice_stability: Mapped[float] = mapped_column(Float, default=0.5)
    thematic_integration: Mapped[float] = mapped_column(Float, default=0.5)
    dialogue_quality: Mapped[float] = mapped_column(Float, default=0.5)
    redundancy_inverse: Mapped[float] = mapped_column(Float, default=0.5)
    stylistic_freshness: Mapped[float] = mapped_column(Float, default=0.5)
    transition_quality: Mapped[float] = mapped_column(Float, default=0.5)
    symbolic_restraint: Mapped[float] = mapped_column(Float, default=0.5)
    device_balance: Mapped[float] = mapped_column(Float, default=0.5)

    # Composite
    composite: Mapped[float] = mapped_column(Float, default=0.5)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
