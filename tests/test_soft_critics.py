"""Tests for soft critics."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from postwriter.llm.budget import TokenBudget
from postwriter.llm.client import LLMClient, LLMResponse
from postwriter.validation.base import ValidationContext, _SOFT_CRITICS
from postwriter.validation.soft.tension import TensionCritic
from postwriter.validation.soft.emotion import EmotionCritic
from postwriter.validation.soft.prose_vitality import ProseVitalityCritic
from postwriter.validation.soft.dialogue import DialogueCritic


def _mock_llm_with_score(score: float, diagnosis: str = "Test diagnosis") -> LLMClient:
    client = MagicMock(spec=LLMClient)
    client.complete = AsyncMock(
        return_value=LLMResponse(
            text=json.dumps({
                "score": score,
                "diagnosis": diagnosis,
                "repair_opportunities": ["Improve X"],
                "confidence": 0.8,
            }),
            tool_use=[],
            input_tokens=400,
            output_tokens=200,
            model="claude-sonnet-4-6",
            stop_reason="end_turn",
        )
    )
    client.budget = TokenBudget()
    return client


def _make_ctx(prose: str = "Test prose.", purpose: str = "Test purpose") -> ValidationContext:
    return ValidationContext(
        prose=prose,
        scene_brief={"purpose": purpose, "conflict": "test conflict", "emotional_turn": "test turn"},
        style_profile={"voice_description": "Terse and controlled."},
    )


def test_all_soft_critics_registered():
    assert len(_SOFT_CRITICS) == 10
    expected = {
        "tension", "emotion", "prose_vitality", "voice_consistency",
        "dialogue", "thematic", "redundancy", "transitions",
        "scene_purpose", "symbolic_restraint",
    }
    assert set(_SOFT_CRITICS.keys()) == expected


@pytest.mark.asyncio
async def test_tension_critic():
    llm = _mock_llm_with_score(0.7, "Good tension management.")
    critic = TensionCritic(llm)
    result = await critic.validate(_make_ctx())

    assert result.is_hard is False
    assert result.passed is None  # Soft critics don't pass/fail
    assert result.score == 0.7
    assert "tension" in result.diagnosis.lower() or result.diagnosis == "Good tension management."


@pytest.mark.asyncio
async def test_emotion_critic():
    llm = _mock_llm_with_score(0.85, "Emotions feel earned.")
    critic = EmotionCritic(llm)
    result = await critic.validate(_make_ctx())

    assert result.score == 0.85


@pytest.mark.asyncio
async def test_prose_vitality_critic():
    llm = _mock_llm_with_score(0.6, "Adequate but unexciting.")
    critic = ProseVitalityCritic(llm)
    result = await critic.validate(_make_ctx())

    assert result.score == 0.6
    assert len(result.repair_opportunities) > 0


@pytest.mark.asyncio
async def test_dialogue_critic():
    llm = _mock_llm_with_score(0.9, "Distinctive voices.")
    critic = DialogueCritic(llm)
    result = await critic.validate(_make_ctx())

    assert result.score == 0.9


@pytest.mark.asyncio
async def test_critic_without_llm():
    critic = TensionCritic(llm=None)
    result = await critic.validate(_make_ctx())

    assert result.score == 0.5  # Default when no LLM
    assert "No LLM" in result.diagnosis


@pytest.mark.asyncio
async def test_critic_handles_bad_json():
    client = MagicMock(spec=LLMClient)
    client.complete = AsyncMock(
        return_value=LLMResponse(
            text="This is not JSON at all.",
            tool_use=[],
            input_tokens=200,
            output_tokens=50,
            model="claude-sonnet-4-6",
            stop_reason="end_turn",
        )
    )
    client.budget = TokenBudget()

    critic = TensionCritic(client)
    result = await critic.validate(_make_ctx())

    # Should gracefully return a default score
    assert result.score == 0.5


@pytest.mark.asyncio
async def test_all_critics_callable():
    """Verify every registered critic can be instantiated and called without LLM."""
    ctx = _make_ctx()
    for name, cls in _SOFT_CRITICS.items():
        critic = cls(llm=None)
        result = await critic.validate(ctx)
        assert result.validator_name == name
        assert result.is_hard is False
