"""Project state detection and persistence.

A .postwriter file in a directory marks it as a postwriter project,
similar to how .git marks a git repository. It stores the manuscript_id
and current phase so the CLI can detect and resume interrupted runs.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from postwriter.types import ManuscriptStatus

PROJECT_FILE = ".postwriter"


@dataclass
class ProjectState:
    """Current state of a postwriter project."""

    manuscript_id: str
    phase: str  # planning, drafting, revising, complete
    profile: str | None = None
    title: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "manuscript_id": self.manuscript_id,
            "phase": self.phase,
            "profile": self.profile,
            "title": self.title,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ProjectState:
        return cls(
            manuscript_id=data["manuscript_id"],
            phase=data.get("phase", "planning"),
            profile=data.get("profile"),
            title=data.get("title", ""),
        )


def detect_project(project_dir: Path) -> ProjectState | None:
    """Check if a directory has an existing postwriter project."""
    state_file = project_dir / PROJECT_FILE
    if not state_file.exists():
        return None
    try:
        data = json.loads(state_file.read_text(encoding="utf-8"))
        return ProjectState.from_dict(data)
    except (json.JSONDecodeError, KeyError):
        return None


def save_project(project_dir: Path, state: ProjectState) -> None:
    """Save project state to the .postwriter file."""
    state_file = project_dir / PROJECT_FILE
    state_file.write_text(
        json.dumps(state.to_dict(), indent=2),
        encoding="utf-8",
    )


def update_phase(project_dir: Path, phase: str) -> None:
    """Update just the phase in an existing project file."""
    state = detect_project(project_dir)
    if state:
        state.phase = phase
        save_project(project_dir, state)
