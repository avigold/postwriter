"""Orchestrator policies: stop conditions, thresholds, and tuning parameters."""

from __future__ import annotations

from dataclasses import dataclass

from postwriter.config import OrchestratorSettings


@dataclass
class ScenePolicy:
    """Policy for scene-level processing."""

    max_repair_rounds: int = 3
    min_improvement_delta: float = 0.02
    acceptance_threshold: float = 0.45  # Minimum composite score to accept without repair
    hard_pass_required: bool = True  # Hard validation must pass before acceptance
    branch_count: int = 3
    pivotal_branch_count: int = 5
    run_soft_critics: bool = False  # Whether to run 10 soft critics (expensive)

    @classmethod
    def from_settings(cls, settings: OrchestratorSettings) -> ScenePolicy:
        # Run soft critics in high_quality mode (more branches + more repair rounds)
        run_soft = settings.max_repair_rounds >= 3 and settings.default_branch_count >= 3
        return cls(
            max_repair_rounds=settings.max_repair_rounds,
            min_improvement_delta=settings.min_improvement_delta,
            branch_count=settings.default_branch_count,
            pivotal_branch_count=settings.pivotal_branch_count,
            run_soft_critics=run_soft,
        )
