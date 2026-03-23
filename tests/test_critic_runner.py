"""Tests for the critic runner."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from postwriter.llm.budget import TokenBudget
from postwriter.llm.client import LLMClient, LLMResponse
from postwriter.orchestrator.critic_runner import CriticRunner
from postwriter.validation.base import ValidationContext


def _mock_llm_for_critics() -> LLMClient:
    """Mock LLM that returns passing results for hard validators and scores for soft critics."""
    client = MagicMock(spec=LLMClient)

    async def mock_complete(**kwargs):
        tier = kwargs.get("tier")
        system = kwargs.get("system", "")

        # Hard validators (Haiku) - return passing
        if tier and tier.value == "haiku":
            return LLMResponse(
                text=json.dumps({"passed": True, "issues": [], "reasoning": "No issues."}),
                tool_use=[], input_tokens=200, output_tokens=100,
                model="claude-haiku-4-5-20251001", stop_reason="end_turn",
            )

        # Soft critics (Sonnet) - return a score
        return LLMResponse(
            text=json.dumps({
                "score": 0.7,
                "diagnosis": "Adequate quality.",
                "repair_opportunities": [],
                "confidence": 0.8,
            }),
            tool_use=[], input_tokens=400, output_tokens=200,
            model="claude-sonnet-4-6", stop_reason="end_turn",
        )

    client.complete = AsyncMock(side_effect=mock_complete)
    client.budget = TokenBudget()
    return client


@pytest.mark.asyncio
async def test_critic_runner_evaluate():
    llm = _mock_llm_for_critics()
    runner = CriticRunner(llm)

    ctx = ValidationContext(
        prose="The harbor lay flat under a low sky. Elena walked toward the terminal.",
        scene_brief={"purpose": "Arrival", "conflict": "Internal reluctance"},
        style_profile={"banned_phrases": []},
    )

    result = await runner.evaluate(ctx)

    # Should have results from both hard and soft
    assert len(result.hard_results) >= 5  # 5 hard validators
    assert len(result.soft_results) >= 10  # 10 soft critics
    assert result.hard_pass is True
    assert result.scores.composite > 0


@pytest.mark.asyncio
async def test_critic_runner_hard_only():
    llm = _mock_llm_for_critics()
    runner = CriticRunner(llm)

    ctx = ValidationContext(
        prose="Test prose.",
        scene_brief={"purpose": "Test"},
        style_profile={},
    )

    result = await runner.evaluate_hard_only(ctx)

    assert len(result.hard_results) >= 5
    assert len(result.soft_results) == 0


@pytest.mark.asyncio
async def test_critic_runner_no_llm():
    runner = CriticRunner(llm=None)

    ctx = ValidationContext(
        prose="The harbor lay flat and gray. Elena walked toward the terminal.",
        scene_brief={"purpose": "Test"},
        style_profile={},
    )

    result = await runner.evaluate(ctx)

    # Hard validators without LLM skip (pass), banned_patterns still works
    assert result.hard_pass is True
    # Soft critics without LLM return 0.5
    for sr in result.soft_results:
        assert sr.score == 0.5


def test_evaluation_result_helpers():
    from postwriter.orchestrator.critic_runner import EvaluationResult
    from postwriter.types import ValidationResult

    er = EvaluationResult(
        hard_results=[
            ValidationResult("banned_patterns", is_hard=True, passed=True, score=None),
            ValidationResult("pov", is_hard=True, passed=False, score=None, diagnosis="POV violation"),
        ],
        soft_results=[
            ValidationResult("tension", is_hard=False, passed=None, score=0.3),
            ValidationResult("emotion", is_hard=False, passed=None, score=0.7),
        ],
    )

    assert len(er.all_results) == 4
    assert len(er.failed_hard()) == 1
    assert er.failed_hard()[0].validator_name == "pov"
    assert len(er.weak_dimensions(threshold=0.4)) == 1
    assert er.weak_dimensions(threshold=0.4)[0].validator_name == "tension"
