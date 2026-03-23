"""Tests for branch comparison and acceptance thresholds."""

from postwriter.scoring.comparison import compare_candidates, _pareto_dominates
from postwriter.scoring.thresholds import AcceptancePolicy, detect_diminishing_returns
from postwriter.scoring.vectors import ScoreVectorData


def test_compare_single_candidate():
    scores = [ScoreVectorData(composite=0.6, hard_pass=True)]
    result = compare_candidates(scores, ["only"])
    assert result.winner_index == 0
    assert result.is_clear_winner


def test_compare_clear_winner():
    scores = [
        ScoreVectorData(composite=0.5, hard_pass=True),
        ScoreVectorData(composite=0.8, hard_pass=True),
        ScoreVectorData(composite=0.6, hard_pass=True),
    ]
    result = compare_candidates(scores, ["a", "b", "c"])
    assert result.winner_index == 1
    assert result.is_clear_winner
    assert result.margin > 0.1


def test_compare_close_call():
    scores = [
        ScoreVectorData(composite=0.71, hard_pass=True),
        ScoreVectorData(composite=0.73, hard_pass=True),
    ]
    result = compare_candidates(scores, ["a", "b"])
    assert result.winner_index == 1
    assert not result.is_clear_winner


def test_compare_prefers_hard_pass():
    scores = [
        ScoreVectorData(composite=0.9, hard_pass=False),
        ScoreVectorData(composite=0.5, hard_pass=True),
    ]
    result = compare_candidates(scores, ["failing", "passing"])
    assert result.winner_index == 1


def test_compare_no_hard_pass():
    scores = [
        ScoreVectorData(composite=0.4, hard_pass=False),
        ScoreVectorData(composite=0.6, hard_pass=False),
    ]
    result = compare_candidates(scores, ["a", "b"])
    assert result.winner_index == 1
    assert not result.is_clear_winner


def test_pareto_dominates():
    a = ScoreVectorData(tension=0.8, emotional_credibility=0.7, prose_vitality=0.6)
    b = ScoreVectorData(tension=0.6, emotional_credibility=0.5, prose_vitality=0.4)
    assert _pareto_dominates(a, b) is True


def test_pareto_not_dominates():
    a = ScoreVectorData(tension=0.8, emotional_credibility=0.3)  # Worse on emotion
    b = ScoreVectorData(tension=0.6, emotional_credibility=0.7)
    assert _pareto_dominates(a, b) is False


def test_acceptance_policy_passes():
    policy = AcceptancePolicy(min_composite=0.5)
    scores = ScoreVectorData(composite=0.7, hard_pass=True)
    assert policy.is_acceptable(scores) is True


def test_acceptance_policy_fails_composite():
    policy = AcceptancePolicy(min_composite=0.5)
    scores = ScoreVectorData(composite=0.3, hard_pass=True)
    assert policy.is_acceptable(scores) is False


def test_acceptance_policy_fails_hard():
    policy = AcceptancePolicy(min_composite=0.3, hard_pass_required=True)
    scores = ScoreVectorData(composite=0.8, hard_pass=False)
    assert policy.is_acceptable(scores) is False


def test_acceptance_policy_dimension_floors():
    policy = AcceptancePolicy(
        min_composite=0.3,
        dimension_floors={"tension": 0.4, "voice_stability": 0.3},
    )
    scores = ScoreVectorData(composite=0.6, tension=0.2, voice_stability=0.5, hard_pass=True)
    assert policy.is_acceptable(scores) is False  # Tension below floor


def test_weakest_dimensions():
    policy = AcceptancePolicy()
    scores = ScoreVectorData(
        tension=0.9, emotional_credibility=0.2, prose_vitality=0.8,
        voice_stability=0.3, dialogue_quality=0.7,
    )
    weakest = policy.weakest_dimensions(scores, n=2)
    assert len(weakest) == 2
    assert weakest[0][0] == "emotional_credibility"
    assert weakest[1][0] == "voice_stability"


def test_diminishing_returns_detected():
    history = [0.40, 0.42, 0.43, 0.435]  # Small improvements
    assert detect_diminishing_returns(history, min_delta=0.02) is True


def test_diminishing_returns_not_detected():
    history = [0.40, 0.50, 0.58]  # Good improvements
    assert detect_diminishing_returns(history, min_delta=0.02) is False


def test_diminishing_returns_short_history():
    history = [0.40]
    assert detect_diminishing_returns(history) is False
