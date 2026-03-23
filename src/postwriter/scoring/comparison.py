"""Branch comparison: multi-criteria selection between draft candidates."""

from __future__ import annotations

from dataclasses import dataclass

from postwriter.scoring.vectors import ScoreVectorData


@dataclass
class ComparisonResult:
    """Result of comparing multiple candidates."""

    winner_index: int
    reason: str
    is_clear_winner: bool  # True if one candidate dominates, False if close call
    margin: float


def compare_candidates(
    scores: list[ScoreVectorData],
    labels: list[str] | None = None,
) -> ComparisonResult:
    """Compare multiple candidates and select the best.

    Uses a combination of:
    1. Hard pass filtering
    2. Composite score ranking
    3. Pareto dominance check for close calls
    """
    if not scores:
        return ComparisonResult(winner_index=0, reason="no candidates", is_clear_winner=False, margin=0.0)

    labels = labels or [f"candidate_{i}" for i in range(len(scores))]

    # Filter to hard-passing candidates
    passing_indices = [i for i, s in enumerate(scores) if s.hard_pass]
    if not passing_indices:
        # None pass hard — pick highest composite anyway
        best_idx = max(range(len(scores)), key=lambda i: scores[i].composite)
        return ComparisonResult(
            winner_index=best_idx,
            reason=f"no hard-passing candidates; {labels[best_idx]} has highest composite",
            is_clear_winner=False,
            margin=0.0,
        )

    # Among passing, rank by composite
    passing_sorted = sorted(passing_indices, key=lambda i: scores[i].composite, reverse=True)
    best_idx = passing_sorted[0]

    if len(passing_sorted) == 1:
        return ComparisonResult(
            winner_index=best_idx,
            reason=f"only hard-passing candidate: {labels[best_idx]}",
            is_clear_winner=True,
            margin=1.0,
        )

    # Check margin between top two
    second_idx = passing_sorted[1]
    margin = scores[best_idx].composite - scores[second_idx].composite

    # Check Pareto dominance
    is_pareto = _pareto_dominates(scores[best_idx], scores[second_idx])

    if margin > 0.1 and is_pareto:
        reason = f"{labels[best_idx]} clearly dominates (margin={margin:.3f}, Pareto dominant)"
        is_clear = True
    elif margin > 0.05:
        reason = f"{labels[best_idx]} leads by {margin:.3f}"
        is_clear = True
    else:
        reason = f"close call: {labels[best_idx]} ({scores[best_idx].composite:.3f}) vs {labels[second_idx]} ({scores[second_idx].composite:.3f})"
        is_clear = False

    return ComparisonResult(
        winner_index=best_idx,
        reason=reason,
        is_clear_winner=is_clear,
        margin=margin,
    )


def _pareto_dominates(a: ScoreVectorData, b: ScoreVectorData) -> bool:
    """Check if candidate 'a' Pareto-dominates 'b' (better or equal on all dimensions)."""
    dims = [
        "tension", "emotional_credibility", "prose_vitality", "voice_stability",
        "thematic_integration", "dialogue_quality", "redundancy_inverse",
        "stylistic_freshness", "transition_quality", "symbolic_restraint",
    ]
    at_least_one_better = False
    for dim in dims:
        va = getattr(a, dim)
        vb = getattr(b, dim)
        if va < vb:
            return False  # Worse on at least one dimension
        if va > vb:
            at_least_one_better = True
    return at_least_one_better
