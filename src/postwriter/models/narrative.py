"""Narrative models: Promise, TimelineEvent, Theme, ThemeManifestation."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from postwriter.models.base import Base, TimestampMixin, UUIDMixin
from postwriter.types import PromiseLinkType, PromiseStatus, PromiseType


class Promise(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "promises"

    manuscript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manuscripts.id", ondelete="CASCADE")
    )
    type: Mapped[PromiseType] = mapped_column(Enum(PromiseType, native_enum=False))
    description: Mapped[str] = mapped_column(Text)
    introducer_scene_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="SET NULL"), nullable=True
    )
    salience: Mapped[float] = mapped_column(Float, default=0.5)
    maturity_window_start: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    maturity_window_end: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    expected_resolution_window: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[PromiseStatus] = mapped_column(
        Enum(PromiseStatus, native_enum=False), default=PromiseStatus.OPEN
    )
    resolution_scene_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="SET NULL"), nullable=True
    )
    payoff_strength: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Relationships
    manuscript: Mapped["Manuscript"] = relationship(back_populates="promises")  # noqa: F821
    scene_links: Mapped[list[PromiseSceneLink]] = relationship(
        back_populates="promise", cascade="all, delete-orphan"
    )


class PromiseSceneLink(UUIDMixin, Base):
    __tablename__ = "promise_scene_links"

    promise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("promises.id", ondelete="CASCADE")
    )
    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE")
    )
    link_type: Mapped[PromiseLinkType] = mapped_column(
        Enum(PromiseLinkType, native_enum=False)
    )

    # Relationships
    promise: Mapped[Promise] = relationship(back_populates="scene_links")


class TimelineEvent(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "timeline_events"

    manuscript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manuscripts.id", ondelete="CASCADE")
    )
    description: Mapped[str] = mapped_column(Text)
    absolute_time: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    relative_time: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    scene_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="SET NULL"), nullable=True
    )
    preconditions: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    consequences: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    knowledge_propagation: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    contradiction_flags: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Relationships
    manuscript: Mapped["Manuscript"] = relationship(back_populates="timeline_events")  # noqa: F821
    participants: Mapped[list[TimelineEventParticipant]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class TimelineEventParticipant(UUIDMixin, Base):
    __tablename__ = "timeline_event_participants"

    event_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("timeline_events.id", ondelete="CASCADE")
    )
    character_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE")
    )
    role: Mapped[str] = mapped_column(
        Enum("participant", "witness", "informed", native_enum=False, name="participant_role")
    )

    # Relationships
    event: Mapped[TimelineEvent] = relationship(back_populates="participants")


class Theme(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "themes"

    manuscript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manuscripts.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(300))
    description: Mapped[str] = mapped_column(Text, default="")
    associated_symbols: Mapped[list[str]] = mapped_column(JSONB, default=list)
    associated_conflicts: Mapped[list[str]] = mapped_column(JSONB, default=list)
    associated_character_tensions: Mapped[list[str]] = mapped_column(JSONB, default=list)
    target_density: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    intensity_by_chapter: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    preferred_embodiment_modes: Mapped[list[str]] = mapped_column(JSONB, default=list)
    overstatement_risk: Mapped[float] = mapped_column(Float, default=0.0)

    # Relationships
    manuscript: Mapped["Manuscript"] = relationship(back_populates="themes")  # noqa: F821
    manifestations: Mapped[list[ThemeManifestation]] = relationship(
        back_populates="theme", cascade="all, delete-orphan"
    )


class ThemeManifestation(UUIDMixin, Base):
    __tablename__ = "theme_manifestations"

    theme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("themes.id", ondelete="CASCADE")
    )
    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE")
    )
    mode: Mapped[str] = mapped_column(String(200))
    intensity: Mapped[float] = mapped_column(Float, default=0.5)
    explicitness: Mapped[float] = mapped_column(Float, default=0.3)

    # Relationships
    theme: Mapped[Theme] = relationship(back_populates="manifestations")
