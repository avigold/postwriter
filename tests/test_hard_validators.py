"""Tests for hard validators."""

import pytest

from postwriter.validation.base import ValidationContext, ValidationSuite, _HARD_VALIDATORS
from postwriter.validation.hard.banned_patterns import BannedPatternsValidator


def test_validators_registered():
    assert "banned_patterns" in _HARD_VALIDATORS
    assert "continuity" in _HARD_VALIDATORS
    assert "pov" in _HARD_VALIDATORS
    assert "timeline" in _HARD_VALIDATORS
    assert "knowledge_state" in _HARD_VALIDATORS


@pytest.mark.asyncio
async def test_banned_patterns_pass():
    validator = BannedPatternsValidator()
    ctx = ValidationContext(
        prose="Elena walked to the window and looked out at the harbor.",
        scene_brief={},
        style_profile={"banned_phrases": ["suddenly", "it was as if"]},
    )
    result = await validator.validate(ctx)
    assert result.passed is True


@pytest.mark.asyncio
async def test_banned_patterns_fail_custom():
    validator = BannedPatternsValidator()
    ctx = ValidationContext(
        prose="Suddenly, she felt a wave of emotion crash over her. It was as if the world had stopped.",
        scene_brief={},
        style_profile={"banned_phrases": ["suddenly", "it was as if"]},
    )
    result = await validator.validate(ctx)
    assert result.passed is False
    assert len(result.evidence) >= 2


@pytest.mark.asyncio
async def test_banned_patterns_catches_ai_tics():
    validator = BannedPatternsValidator()
    ctx = ValidationContext(
        prose="She couldn't help but notice a sense of dread. In that moment, everything changed.",
        scene_brief={},
        style_profile={},  # Even without custom bans, AI tics should be caught
    )
    result = await validator.validate(ctx)
    assert result.passed is False
    # Should catch "couldn't help but", "a sense of", "in that moment", "everything changed"
    assert len(result.evidence) >= 3


@pytest.mark.asyncio
async def test_banned_patterns_clean_prose():
    validator = BannedPatternsValidator()
    ctx = ValidationContext(
        prose=(
            "The harbor lay flat under a low sky. Elena pulled her coat tighter "
            "and walked toward the ferry terminal. Salt air stung her eyes. "
            "She hadn't been here in eleven years."
        ),
        scene_brief={},
        style_profile={"banned_phrases": ["suddenly", "it was as if", "she realized"]},
    )
    result = await validator.validate(ctx)
    assert result.passed is True


@pytest.mark.asyncio
async def test_validation_suite_no_llm():
    """Without an LLM, model-based validators should pass (skip gracefully)."""
    suite = ValidationSuite(llm=None)
    ctx = ValidationContext(
        prose="Test prose.",
        scene_brief={"location": "Harbor"},
        style_profile={},
    )
    results = await suite.run_hard(ctx)
    # All should pass since LLM-dependent validators skip without LLM
    for r in results:
        assert r.passed is True or r.passed is None


def test_validation_suite_discovers_validators():
    suite = ValidationSuite()
    validators = suite.get_hard_validators()
    assert len(validators) >= 5
    names = {v.name for v in validators}
    assert "banned_patterns" in names
    assert "continuity" in names
