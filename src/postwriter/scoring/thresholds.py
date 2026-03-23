"""Acceptance thresholds and diminishing returns detection."""

from __future__ import annotations

from dataclasses import dataclass

from postwriter.scoring.vectors import ScoreVectorData


@dataclass
class AcceptancePolicy:
    """Defines when a draft is good enough to accept."""

    min_composite: float = 0.45
    hard_pass_required: bool = True
    # Per-dimension minimums (below these triggers repair even if composite is ok)
    dimension_floors: dict[str, float] | None = None

    def is_acceptable(self, scores: ScoreVectorData) -> bool:
        """Check if scores meet acceptance criteria."""
        if self.hard_pass_required and not scores.hard_pass:
            return False
        if scores.composite < self.min_composite:
            return False
        if self.dimension_floors:
            for dim, floor in self.dimension_floors.items():
                val = getattr(scores, dim, 0.5)
                if val < floor:
                    return False
        return True

    def weakest_dimensions(self, scores: ScoreVectorData, n: int = 3) -> list[tuple[str, float]]:
        """Return the n weakest scoring dimensions."""
        dims = [
            ("tension", scores.tension),
            ("emotional_credibility", scores.emotional_credibility),
            ("prose_vitality", scores.prose_vitality),
            ("voice_stability", scores.voice_stability),
            ("thematic_integration", scores.thematic_integration),
            ("dialogue_quality", scores.dialogue_quality),
            ("redundancy_inverse", scores.redundancy_inverse),
            ("stylistic_freshness", scores.stylistic_freshness),
            ("transition_quality", scores.transition_quality),
            ("symbolic_restraint", scores.symbolic_restraint),
        ]
        dims.sort(key=lambda x: x[1])
        return dims[:n]


def detect_diminishing_returns(
    score_history: list[float],
    min_delta: float = 0.02,
    lookback: int = 2,
) -> bool:
    """Detect if recent repair rounds are producing diminishing returns."""
    if len(score_history) < lookback + 1:
        return False
    recent_deltas = [
        score_history[i] - score_history[i - 1]
        for i in range(len(score_history) - lookback, len(score_history))
    ]
    return all(d < min_delta for d in recent_deltas)
