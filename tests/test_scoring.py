"""Tests for the scoring system."""

from postwriter.scoring.vectors import ScoreVectorData, compute_composite, scores_from_validation
from postwriter.types import ValidationResult


def test_score_vector_defaults():
    sv = ScoreVectorData()
    assert sv.hard_pass is True
    assert sv.composite == 0.5


def test_compute_composite():
    sv = ScoreVectorData(
        tension=0.8,
        emotional_credibility=0.7,
        prose_vitality=0.9,
        voice_stability=0.6,
    )
    score = sv.compute_composite()
    assert 0.0 < score < 1.0
    assert sv.composite == score


def test_compute_composite_custom_weights():
    sv = ScoreVectorData(tension=1.0, emotional_credibility=0.0)
    # Weight tension heavily
    score = sv.compute_composite(weights={
        "tension": 1.0,
        "emotional_credibility": 1.0,
    })
    assert score == 0.5  # Average of 1.0 and 0.0


def test_scores_from_hard_validation():
    results = [
        ValidationResult(
            validator_name="banned_patterns", is_hard=True, passed=True, score=None,
        ),
        ValidationResult(
            validator_name="continuity", is_hard=True, passed=True, score=None,
        ),
    ]
    sv = scores_from_validation(results)
    assert sv.hard_pass is True


def test_scores_from_hard_failure():
    results = [
        ValidationResult(
            validator_name="banned_patterns", is_hard=True, passed=False, score=None,
            diagnosis="Banned phrase found",
        ),
    ]
    sv = scores_from_validation(results)
    assert sv.hard_pass is False


def test_scores_from_soft_critics():
    results = [
        ValidationResult(
            validator_name="tension", is_hard=False, passed=None, score=0.8,
        ),
        ValidationResult(
            validator_name="emotion", is_hard=False, passed=None, score=0.6,
        ),
    ]
    sv = scores_from_validation(results)
    assert sv.tension == 0.8
    assert sv.emotional_credibility == 0.6
    assert sv.hard_pass is True  # No hard failures


def test_score_vector_to_dict():
    sv = ScoreVectorData(hard_pass=True, tension=0.7)
    sv.compute_composite()
    d = sv.to_dict()
    assert d["hard_pass"] is True
    assert d["tension"] == 0.7
    assert "composite" in d
