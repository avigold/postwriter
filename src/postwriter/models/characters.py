"""Character models: Character, CharacterSceneState, CharacterRelationship."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy import Boolean, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from postwriter.models.base import Base, TimestampMixin, UUIDMixin


class Character(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "characters"

    manuscript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manuscripts.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column(String(300))
    aliases: Mapped[list[str]] = mapped_column(JSONB, default=list)
    age: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    biography: Mapped[str] = mapped_column(Text, default="")
    motives: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    fears: Mapped[list[str]] = mapped_column(JSONB, default=list)
    desires: Mapped[list[str]] = mapped_column(JSONB, default=list)
    secrets: Mapped[list[str]] = mapped_column(JSONB, default=list)
    social_position: Mapped[str] = mapped_column(Text, default="")
    speaking_traits: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    movement_traits: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    recurring_gestures: Mapped[list[str]] = mapped_column(JSONB, default=list)
    moral_constraints: Mapped[list[str]] = mapped_column(JSONB, default=list)
    arc_hypotheses: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    arc_history: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, default=list)
    is_pov_character: Mapped[bool] = mapped_column(Boolean, default=False)

    # Relationships
    manuscript: Mapped["Manuscript"] = relationship(back_populates="characters")  # noqa: F821
    scene_states: Mapped[list[CharacterSceneState]] = relationship(
        back_populates="character", cascade="all, delete-orphan"
    )


class CharacterSceneState(UUIDMixin, Base):
    __tablename__ = "character_scene_states"

    character_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE")
    )
    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE")
    )
    knowledge_state: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    emotional_state: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    intention_state: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    unresolved_pressures: Mapped[list[str]] = mapped_column(JSONB, default=list)
    arc_position: Mapped[str] = mapped_column(Text, default="")

    # Relationships
    character: Mapped[Character] = relationship(back_populates="scene_states")
    scene: Mapped["Scene"] = relationship(back_populates="character_states")  # noqa: F821


class CharacterRelationship(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "character_relationships"

    manuscript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manuscripts.id", ondelete="CASCADE")
    )
    character_a_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE")
    )
    character_b_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("characters.id", ondelete="CASCADE")
    )
    relationship_type: Mapped[str] = mapped_column(String(200))
    description: Mapped[str] = mapped_column(Text, default="")
    intensity: Mapped[float] = mapped_column(Float, default=0.5)
    # Scene where this relationship state was established/last changed
    scene_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="SET NULL"), nullable=True
    )
    status: Mapped[str] = mapped_column(
        Enum("active", "ended", "transformed", native_enum=False, name="rel_status"),
        default="active",
    )
