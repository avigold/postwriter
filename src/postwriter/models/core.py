"""Core structural models: Manuscript, Act, Chapter, Scene, SceneDraft, SceneDependency."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy import Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from postwriter.models.base import Base, TimestampMixin, UUIDMixin
from postwriter.types import BranchStatus, DependencyType, ManuscriptStatus, SceneStatus


class Manuscript(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "manuscripts"

    title: Mapped[str] = mapped_column(String(500), default="Untitled")
    premise: Mapped[str] = mapped_column(Text, default="")
    controlling_design: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    status: Mapped[ManuscriptStatus] = mapped_column(
        Enum(ManuscriptStatus, native_enum=False),
        default=ManuscriptStatus.BOOTSTRAPPING,
    )

    # Relationships
    acts: Mapped[list[Act]] = relationship(
        back_populates="manuscript", cascade="all, delete-orphan", order_by="Act.ordinal"
    )
    characters: Mapped[list["Character"]] = relationship(  # noqa: F821
        back_populates="manuscript", cascade="all, delete-orphan"
    )
    promises: Mapped[list["Promise"]] = relationship(  # noqa: F821
        back_populates="manuscript", cascade="all, delete-orphan"
    )
    themes: Mapped[list["Theme"]] = relationship(  # noqa: F821
        back_populates="manuscript", cascade="all, delete-orphan"
    )
    style_profiles: Mapped[list["StyleProfile"]] = relationship(  # noqa: F821
        back_populates="manuscript", cascade="all, delete-orphan"
    )
    timeline_events: Mapped[list["TimelineEvent"]] = relationship(  # noqa: F821
        back_populates="manuscript", cascade="all, delete-orphan"
    )


class Act(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "acts"

    manuscript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manuscripts.id", ondelete="CASCADE")
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String(500), default="")
    purpose: Mapped[str] = mapped_column(Text, default="")
    emotional_arc: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Relationships
    manuscript: Mapped[Manuscript] = relationship(back_populates="acts")
    chapters: Mapped[list[Chapter]] = relationship(
        back_populates="act", cascade="all, delete-orphan", order_by="Chapter.ordinal"
    )


class Chapter(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "chapters"

    manuscript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manuscripts.id", ondelete="CASCADE")
    )
    act_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("acts.id", ondelete="CASCADE")
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    title: Mapped[str] = mapped_column(String(500), default="")
    function: Mapped[str] = mapped_column(Text, default="")
    emotional_contour_target: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    transition_profile: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    opening_pressure: Mapped[float] = mapped_column(Float, default=0.5)
    closing_pressure: Mapped[float] = mapped_column(Float, default=0.5)
    thematic_density_target: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    rhythm_profile: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    motif_target: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Relationships
    manuscript: Mapped[Manuscript] = relationship()
    act: Mapped[Act] = relationship(back_populates="chapters")
    scenes: Mapped[list[Scene]] = relationship(
        back_populates="chapter", cascade="all, delete-orphan", order_by="Scene.ordinal"
    )


class Scene(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "scenes"

    chapter_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE")
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    pov_character_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("characters.id", ondelete="SET NULL"), nullable=True
    )
    location: Mapped[str] = mapped_column(Text, default="")
    time_marker: Mapped[str] = mapped_column(String(200), default="")
    purpose: Mapped[str] = mapped_column(Text, default="")
    conflict: Mapped[str] = mapped_column(Text, default="")
    stakes: Mapped[str] = mapped_column(Text, default="")
    revelation: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    emotional_turn: Mapped[str] = mapped_column(Text, default="")
    dramatic_function: Mapped[str] = mapped_column(String(200), default="")
    expected_stylistic_profile: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    expected_device_functions: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    prohibited_moves: Mapped[list[str]] = mapped_column(JSONB, default=list)
    themes_touched: Mapped[list[str]] = mapped_column(JSONB, default=list)
    symbols_touched: Mapped[list[str]] = mapped_column(JSONB, default=list)
    is_pivotal: Mapped[bool] = mapped_column(default=False)
    status: Mapped[SceneStatus] = mapped_column(
        Enum(SceneStatus, native_enum=False), default=SceneStatus.PENDING
    )
    accepted_draft_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), nullable=True
    )

    # Relationships
    chapter: Mapped[Chapter] = relationship(back_populates="scenes")
    drafts: Mapped[list[SceneDraft]] = relationship(
        back_populates="scene", cascade="all, delete-orphan"
    )
    character_states: Mapped[list["CharacterSceneState"]] = relationship(  # noqa: F821
        back_populates="scene", cascade="all, delete-orphan"
    )
    state_mutations: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)


class SceneDraft(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "scene_drafts"

    scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE")
    )
    branch_label: Mapped[str] = mapped_column(String(200), default="default")
    version: Mapped[int] = mapped_column(Integer, default=1)
    prose: Mapped[str] = mapped_column(Text, default="")
    word_count: Mapped[int] = mapped_column(Integer, default=0)
    branch_status: Mapped[BranchStatus] = mapped_column(
        Enum(BranchStatus, native_enum=False), default=BranchStatus.ACTIVE
    )

    # Relationships
    scene: Mapped[Scene] = relationship(back_populates="drafts")


class SceneDependency(UUIDMixin, Base):
    __tablename__ = "scene_dependencies"

    source_scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE")
    )
    target_scene_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("scenes.id", ondelete="CASCADE")
    )
    dependency_type: Mapped[DependencyType] = mapped_column(
        Enum(DependencyType, native_enum=False)
    )
    description: Mapped[str] = mapped_column(Text, default="")
