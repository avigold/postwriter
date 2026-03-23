"""Repair action specifications."""

from __future__ import annotations

from dataclasses import dataclass, field

from postwriter.types import RepairPriority


@dataclass
class RepairActionSpec:
    """A single repair action to be executed by the local rewriter."""

    priority: RepairPriority
    target_dimension: str
    instruction: str
    preserve_constraints: list[str] = field(default_factory=list)
    allowed_interventions: list[str] = field(default_factory=list)
    banned_interventions: list[str] = field(default_factory=list)
    # Reference back to the validation issue that triggered this
    issue_diagnosis: str = ""
    issue_evidence: list[dict[str, str]] = field(default_factory=list)
