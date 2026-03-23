"""Configuration profiles for different generation strategies."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from postwriter.config import LLMSettings, OrchestratorSettings


@dataclass
class Profile:
    """A named configuration profile."""

    name: str
    description: str
    orchestrator: dict[str, Any]
    llm: dict[str, Any] | None = None


PROFILES: dict[str, Profile] = {
    "fast_draft": Profile(
        name="fast_draft",
        description="Quick first draft: fewer branches, fewer repair rounds, Sonnet for everything.",
        orchestrator={
            "max_repair_rounds": 1,
            "default_branch_count": 2,
            "pivotal_branch_count": 3,
            "min_improvement_delta": 0.05,
        },
    ),
    "high_quality": Profile(
        name="high_quality",
        description="Maximum quality: more branches, more repair rounds, Opus for pivotal scenes.",
        orchestrator={
            "max_repair_rounds": 5,
            "default_branch_count": 3,
            "pivotal_branch_count": 5,
            "min_improvement_delta": 0.01,
        },
    ),
    "budget_conscious": Profile(
        name="budget_conscious",
        description="Minimize API costs: Haiku where possible, fewer branches, minimal repair.",
        orchestrator={
            "max_repair_rounds": 1,
            "default_branch_count": 2,
            "pivotal_branch_count": 2,
            "min_improvement_delta": 0.1,
        },
    ),
}


def apply_profile(
    profile_name: str,
    orchestrator_settings: OrchestratorSettings,
    llm_settings: LLMSettings | None = None,
) -> None:
    """Apply a named profile to settings objects (mutates in place)."""
    profile = PROFILES.get(profile_name)
    if not profile:
        raise ValueError(f"Unknown profile: {profile_name}. Available: {list(PROFILES.keys())}")

    for key, value in profile.orchestrator.items():
        if hasattr(orchestrator_settings, key):
            setattr(orchestrator_settings, key, value)

    if profile.llm and llm_settings:
        for key, value in profile.llm.items():
            if hasattr(llm_settings, key):
                setattr(llm_settings, key, value)


def list_profiles() -> list[dict[str, str]]:
    """Return list of available profiles with descriptions."""
    return [
        {"name": p.name, "description": p.description}
        for p in PROFILES.values()
    ]
