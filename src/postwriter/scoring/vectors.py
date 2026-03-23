"""Score vector computation and composite scoring."""

from __future__ import annotations

from dataclasses import dataclass, field

from postwriter.types import ValidationResult

# Default weights for composite scoring
DEFAULT_WEIGHTS: dict[str, float] = {
    "tension": 0.12,
    "emotional_credibility": 0.12,
    "prose_vitality": 0.10,
    "voice_stability": 0.10,
    "thematic_integration": 0.08,
    "dialogue_quality": 0.10,
    "redundancy_inverse": 0.08,
    "stylistic_freshness": 0.10,
    "transition_quality": 0.08,
    "symbolic_restraint": 0.06,
    "device_balance": 0.06,
}


@dataclass
class ScoreVectorData:
    """Score vector for a single draft."""

    hard_pass: bool = True

    # Soft dimensions (0.0-1.0)
    tension: float = 0.5
    emotional_credibility: float = 0.5
    prose_vitality: float = 0.5
    voice_stability: float = 0.5
    thematic_integration: float = 0.5
    dialogue_quality: float = 0.5
    redundancy_inverse: float = 0.5
    stylistic_freshness: float = 0.5
    transition_quality: float = 0.5
    symbolic_restraint: float = 0.5
    device_balance: float = 0.5

    # Composite
    composite: float = 0.5

    def compute_composite(self, weights: dict[str, float] | None = None) -> float:
        """Compute weighted composite score."""
        w = weights or DEFAULT_WEIGHTS
        total = 0.0
        weight_sum = 0.0
        for dim, weight in w.items():
            val = getattr(self, dim, 0.5)
            total += val * weight
            weight_sum += weight
        self.composite = total / weight_sum if weight_sum > 0 else 0.5
        return self.composite

    def to_dict(self) -> dict[str, float | bool]:
        return {
            "hard_pass": self.hard_pass,
            "tension": self.tension,
            "emotional_credibility": self.emotional_credibility,
            "prose_vitality": self.prose_vitality,
            "voice_stability": self.voice_stability,
            "thematic_integration": self.thematic_integration,
            "dialogue_quality": self.dialogue_quality,
            "redundancy_inverse": self.redundancy_inverse,
            "stylistic_freshness": self.stylistic_freshness,
            "transition_quality": self.transition_quality,
            "symbolic_restraint": self.symbolic_restraint,
            "device_balance": self.device_balance,
            "composite": self.composite,
        }


def scores_from_validation(results: list[ValidationResult]) -> ScoreVectorData:
    """Build a score vector from validation results."""
    sv = ScoreVectorData()

    for r in results:
        if r.is_hard:
            if r.passed is False:
                sv.hard_pass = False
        else:
            # Map soft critic scores to dimensions
            if r.score is not None:
                dim_map: dict[str, str] = {
                    "tension": "tension",
                    "emotion": "emotional_credibility",
                    "prose_vitality": "prose_vitality",
                    "voice_consistency": "voice_stability",
                    "dialogue": "dialogue_quality",
                    "thematic": "thematic_integration",
                    "redundancy": "redundancy_inverse",
                    "transitions": "transition_quality",
                    "scene_purpose": "tension",  # maps to closest
                    "symbolic_restraint": "symbolic_restraint",
                }
                dim = dim_map.get(r.validator_name)
                if dim and hasattr(sv, dim):
                    setattr(sv, dim, r.score)

    sv.compute_composite()
    return sv


def compute_composite(scores: ScoreVectorData, weights: dict[str, float] | None = None) -> float:
    """Convenience function to compute composite score."""
    return scores.compute_composite(weights)
