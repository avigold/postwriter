"""Style profile model."""

from __future__ import annotations

import uuid
from typing import Any, Optional

from sqlalchemy import Boolean, Float, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from postwriter.models.base import Base, TimestampMixin, UUIDMixin


class StyleProfile(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "style_profiles"

    manuscript_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("manuscripts.id", ondelete="CASCADE")
    )
    is_default: Mapped[bool] = mapped_column(Boolean, default=True)
    # If set, this profile overrides the default for a specific chapter
    chapter_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("chapters.id", ondelete="CASCADE"), nullable=True
    )

    voice_description: Mapped[str] = mapped_column(Text, default="")
    directness: Mapped[float] = mapped_column(Float, default=0.5)
    subtext_target: Mapped[float] = mapped_column(Float, default=0.5)
    irony_target: Mapped[float] = mapped_column(Float, default=0.3)
    lyricism_target: Mapped[float] = mapped_column(Float, default=0.4)

    sentence_length_bands: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    sentence_variance_bands: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    dialogue_density_band: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    metaphor_density_band: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    simile_density_band: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    fragment_tolerance: Mapped[float] = mapped_column(Float, default=0.3)
    exposition_tolerance: Mapped[float] = mapped_column(Float, default=0.4)
    abstraction_tolerance: Mapped[float] = mapped_column(Float, default=0.3)

    preferred_imagery_domains: Mapped[list[str]] = mapped_column(JSONB, default=list)
    banned_imagery_domains: Mapped[list[str]] = mapped_column(JSONB, default=list)
    banned_phrases: Mapped[list[str]] = mapped_column(JSONB, default=list)
    banned_moves: Mapped[list[str]] = mapped_column(JSONB, default=list)
    disfavoured_devices: Mapped[list[str]] = mapped_column(JSONB, default=list)
    recurrence_caps: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)
    chapter_modulation_rules: Mapped[dict[str, Any]] = mapped_column(JSONB, default=dict)

    # Relationships
    manuscript: Mapped["Manuscript"] = relationship(back_populates="style_profiles")  # noqa: F821
