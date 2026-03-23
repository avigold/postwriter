"""Tests for the repair planner."""

from postwriter.repair.planner import RepairPlanner
from postwriter.types import RepairPriority, ValidationResult


def test_plan_from_hard_failures():
    planner = RepairPlanner()

    results = [
        ValidationResult(
            validator_name="banned_patterns",
            is_hard=True,
            passed=False,
            score=None,
            diagnosis="Found 2 banned phrases",
            evidence=[
                {"type": "banned_phrase", "phrase": "suddenly"},
                {"type": "ai_tic", "phrase": "a sense of"},
            ],
        ),
        ValidationResult(
            validator_name="pov",
            is_hard=True,
            passed=False,
            score=None,
            diagnosis="Non-POV character thoughts narrated",
            evidence=[{"character": "Marcus", "description": "thoughts accessed"}],
        ),
        ValidationResult(
            validator_name="continuity",
            is_hard=True,
            passed=True,
            score=None,
            diagnosis="No issues",
        ),
    ]

    actions = planner.plan(results)
    assert len(actions) == 2  # Only failures generate actions

    # Should be sorted by priority
    assert actions[0].priority == RepairPriority.HARD_LEGALITY
    assert actions[1].priority == RepairPriority.HARD_LEGALITY


def test_plan_skips_passing():
    planner = RepairPlanner()

    results = [
        ValidationResult(
            validator_name="banned_patterns", is_hard=True, passed=True,
            score=None, diagnosis="Clean",
        ),
        ValidationResult(
            validator_name="continuity", is_hard=True, passed=True,
            score=None, diagnosis="Clean",
        ),
    ]

    actions = planner.plan(results)
    assert len(actions) == 0


def test_plan_priority_ordering():
    planner = RepairPlanner()

    results = [
        ValidationResult(
            validator_name="knowledge_state", is_hard=True, passed=False,
            score=None, diagnosis="Knowledge leak",
        ),
        ValidationResult(
            validator_name="banned_patterns", is_hard=True, passed=False,
            score=None, diagnosis="Banned phrase",
            evidence=[{"phrase": "suddenly"}],
        ),
    ]

    actions = planner.plan(results)
    assert len(actions) == 2
    # Hard legality (banned_patterns) should come before knowledge state
    assert actions[0].priority.value <= actions[1].priority.value


def test_banned_pattern_action_detail():
    planner = RepairPlanner()

    results = [
        ValidationResult(
            validator_name="banned_patterns", is_hard=True, passed=False,
            score=None, diagnosis="Found banned phrases",
            evidence=[
                {"type": "banned_phrase", "phrase": "suddenly"},
                {"type": "ai_tic", "phrase": "a wave of"},
            ],
        ),
    ]

    actions = planner.plan(results)
    assert len(actions) == 1
    assert "suddenly" in actions[0].instruction
    assert "emotional_force" in actions[0].preserve_constraints
