"""Base classes for revision passes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol


@dataclass
class RevisionProposal:
    """A proposed revision from an audit pass."""

    audit_name: str
    severity: float  # 0-1, higher = more critical
    description: str
    target_scene_ids: list[str] = field(default_factory=list)
    target_chapter_ids: list[str] = field(default_factory=list)
    proposed_action: str = ""
    risk: str = ""  # Description of what could go wrong
    requires_human_approval: bool = False
    evidence: dict[str, Any] = field(default_factory=dict)


class RevisionPass(Protocol):
    """Protocol for global revision audit passes."""

    name: str

    async def audit(self, manuscript_data: dict[str, Any]) -> list[RevisionProposal]: ...
