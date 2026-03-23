"""Tests for scene writer and branch profiles."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from postwriter.agents.branch_profiles import (
    BRANCH_PROFILES,
    BranchProfile,
    apply_profile_modifiers,
    get_branch_profiles,
)
from postwriter.agents.scene_writer import SceneWriter
from postwriter.llm.budget import TokenBudget
from postwriter.llm.client import LLMClient, LLMResponse
from postwriter.types import AgentContext


def test_branch_profiles_exist():
    assert len(BRANCH_PROFILES) >= 7
    assert "restrained_subtext_heavy" in BRANCH_PROFILES
    assert "lyrical_image_forward" in BRANCH_PROFILES
    assert "sparse_pressure_through_silence" in BRANCH_PROFILES


def test_get_branch_profiles_default():
    profiles = get_branch_profiles(count=3)
    assert len(profiles) == 3
    labels = {p.label for p in profiles}
    assert "restrained_subtext_heavy" in labels


def test_get_branch_profiles_pivotal():
    profiles = get_branch_profiles(count=5, is_pivotal=True)
    assert len(profiles) == 5


def test_apply_profile_modifiers():
    base = {"directness": 0.5, "lyricism_target": 0.5, "subtext_target": 0.5}
    profile = BRANCH_PROFILES["restrained_subtext_heavy"]
    modified = apply_profile_modifiers(base, profile)

    # Should be clamped to 0-1
    assert 0.0 <= modified["directness"] <= 1.0
    assert modified["subtext_target"] > base["subtext_target"]  # Should increase


def test_apply_profile_modifiers_clamping():
    base = {"directness": 0.1, "lyricism_target": 0.9}
    profile = BranchProfile(
        label="test",
        description="test",
        modifiers={"directness": -0.5, "lyricism_target": +0.5},
        writing_instructions="test",
    )
    modified = apply_profile_modifiers(base, profile)
    assert modified["directness"] == 0.0  # Clamped to 0
    assert modified["lyricism_target"] == 1.0  # Clamped to 1


@pytest.mark.asyncio
async def test_scene_writer_returns_prose():
    client = MagicMock(spec=LLMClient)
    client.complete = AsyncMock(
        return_value=LLMResponse(
            text="The door opened slowly. Elena stepped inside, her eyes adjusting to the dim light.",
            tool_use=[],
            input_tokens=500,
            output_tokens=200,
            model="claude-sonnet-4-6",
            stop_reason="end_turn",
        )
    )
    client.budget = TokenBudget()

    writer = SceneWriter(client)
    ctx = AgentContext(
        manuscript_id="test",
        scene_brief={
            "purpose": "Establish arrival",
            "conflict": "Internal reluctance",
            "emotional_turn": "reluctance to resolve",
        },
    )

    result = await writer.execute(ctx)
    assert result.success
    # Scene writer returns raw text, not parsed structured output
    assert "Elena" in result.raw_response


@pytest.mark.asyncio
async def test_scene_writer_with_branch_profile():
    client = MagicMock(spec=LLMClient)
    client.complete = AsyncMock(
        return_value=LLMResponse(
            text="Silence. The room held its breath.",
            tool_use=[],
            input_tokens=500,
            output_tokens=100,
            model="claude-sonnet-4-6",
            stop_reason="end_turn",
        )
    )
    client.budget = TokenBudget()

    profile = BRANCH_PROFILES["sparse_pressure_through_silence"]
    writer = SceneWriter(client, branch_profile=profile)

    ctx = AgentContext(manuscript_id="test", scene_brief={"purpose": "test"})
    result = await writer.execute(ctx)
    assert result.success

    # Verify the system prompt includes the branch profile instructions
    call_kwargs = client.complete.call_args
    system_prompt = call_kwargs.kwargs.get("system") or call_kwargs[1].get("system", "")
    assert "sparse_pressure_through_silence" in system_prompt
