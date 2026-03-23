"""Tests for planning agents with mocked LLM responses."""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest

from postwriter.agents.architect import PremiseArchitect, PremiseResponse, SpineArchitect
from postwriter.agents.character_designer import CharacterDesigner
from postwriter.agents.chapter_planner import ChapterPlanner
from postwriter.agents.promise_seeder import PromiseSeeder
from postwriter.agents.scene_planner import ScenePlanner
from postwriter.agents.style_builder import StyleBuilder
from postwriter.llm.budget import TokenBudget
from postwriter.llm.client import LLMClient, LLMResponse
from postwriter.types import AgentContext, ModelTier


def _mock_llm(tool_response: dict) -> LLMClient:
    """Create a mock LLM that returns a tool_use response."""
    client = MagicMock(spec=LLMClient)
    client.complete = AsyncMock(
        return_value=LLMResponse(
            text="",
            tool_use=[{"id": "1", "name": "respond", "input": tool_response}],
            input_tokens=500,
            output_tokens=300,
            model="claude-opus-4-6",
            stop_reason="tool_use",
        )
    )
    client.budget = TokenBudget()
    return client


@pytest.mark.asyncio
async def test_premise_architect():
    response_data = {
        "premise": "A retired forensic linguist returns to her coastal hometown...",
        "controlling_design": {
            "central_question": "Can language reveal what silence conceals?",
            "arc_shape": "descent and partial recovery",
            "turning_points": ["discovery of letters", "betrayal revealed"],
            "emotional_trajectory": "unease → dread → grief → uneasy acceptance",
            "plot_internal_relationship": "External mystery mirrors internal reckoning",
            "tonal_range": "atmospheric tension with moments of dark intimacy",
        },
        "thematic_architecture": {
            "character_tensions": ["truth vs loyalty"],
            "symbolic_patterns": ["water and erosion"],
            "structural_embodiments": ["fragmented timeline mirrors fragmented truth"],
        },
    }

    llm = _mock_llm(response_data)
    agent = PremiseArchitect(llm)

    ctx = AgentContext(
        manuscript_id="test",
        extra={
            "creative_brief": {
                "genre": "literary thriller",
                "setting": "Coastal Maine",
                "time_period": "present day",
                "tone": "atmospheric",
                "protagonist": "A retired forensic linguist",
                "central_conflict": "Sister's disappearance",
                "ending_direction": "Ambiguous",
            }
        },
    )

    result = await agent.execute(ctx)
    assert result.success
    assert result.model_tier == ModelTier.OPUS
    assert isinstance(result.parsed, PremiseResponse)
    assert "linguist" in result.parsed.premise


@pytest.mark.asyncio
async def test_spine_architect():
    response_data = {
        "acts": [
            {"name": "Arrival", "ordinal": 1, "purpose": "Setup", "emotional_arc": {}, "chapter_count": 10},
            {"name": "Investigation", "ordinal": 2, "purpose": "Escalation", "emotional_arc": {}, "chapter_count": 15},
            {"name": "Reckoning", "ordinal": 3, "purpose": "Resolution", "emotional_arc": {}, "chapter_count": 10},
        ],
        "major_turning_points": [
            {"description": "Discovery", "approximate_position": "end of act 1", "function": "revelation"},
        ],
        "arc_summary": "A descent into family secrets followed by painful clarity.",
    }

    llm = _mock_llm(response_data)
    agent = SpineArchitect(llm)
    ctx = AgentContext(
        manuscript_id="test",
        premise="A linguist returns home...",
        controlling_design={"central_question": "test"},
    )

    result = await agent.execute(ctx)
    assert result.success
    assert len(result.parsed.acts) == 3


@pytest.mark.asyncio
async def test_character_designer():
    response_data = {
        "characters": [
            {
                "name": "Elena Voss",
                "aliases": [],
                "age": "52",
                "biography": "A retired professor.",
                "motives": {"primary": "truth"},
                "fears": ["irrelevance"],
                "desires": ["understanding"],
                "secrets": ["She knew more than she claimed"],
                "social_position": "Former academic",
                "speaking_traits": {"pattern": "precise"},
                "movement_traits": {},
                "recurring_gestures": [],
                "moral_constraints": ["Won't betray a source"],
                "arc_hypothesis": "From denial to acceptance",
                "is_pov_character": True,
                "relationships": [],
            }
        ],
        "relationship_dynamics": "The cast creates tension through conflicting loyalties.",
    }

    llm = _mock_llm(response_data)
    agent = CharacterDesigner(llm)
    ctx = AgentContext(manuscript_id="test", premise="Test premise")

    result = await agent.execute(ctx)
    assert result.success
    assert result.parsed.characters[0].name == "Elena Voss"


@pytest.mark.asyncio
async def test_style_builder():
    response_data = {
        "voice_description": "Terse and observational.",
        "directness": 0.7,
        "subtext_target": 0.6,
        "irony_target": 0.3,
        "lyricism_target": 0.3,
        "sentence_length_bands": {"short_pct": 30, "medium_pct": 50, "long_pct": 20},
        "dialogue_density_band": {"min_pct": 20, "max_pct": 50, "target_pct": 35},
        "metaphor_density_band": {"min_per_1000": 1, "max_per_1000": 4},
        "fragment_tolerance": 0.4,
        "exposition_tolerance": 0.3,
        "abstraction_tolerance": 0.2,
        "preferred_imagery_domains": ["architecture", "water"],
        "banned_imagery_domains": [],
        "banned_phrases": ["suddenly", "it was as if"],
        "banned_moves": ["mirror description"],
        "disfavoured_devices": [],
        "recurrence_caps": {"rhetorical_question": 3},
    }

    llm = _mock_llm(response_data)
    agent = StyleBuilder(llm)
    ctx = AgentContext(
        manuscript_id="test",
        premise="Test",
        extra={"creative_brief": {"genre": "thriller", "tone": "tense"}},
    )

    result = await agent.execute(ctx)
    assert result.success
    assert result.parsed.directness == 0.7
    assert "suddenly" in result.parsed.banned_phrases


@pytest.mark.asyncio
async def test_chapter_planner():
    response_data = {
        "chapters": [
            {
                "ordinal": 1,
                "title": "Arrival",
                "function": "Introduce setting and protagonist",
                "emotional_contour": {"opening_emotion": "unease", "arc_shape": "rising tension"},
                "opening_pressure": 0.3,
                "closing_pressure": 0.5,
                "scene_count": 3,
                "scene_summaries": ["Elena arrives", "Explores town", "First encounter"],
                "themes_active": ["isolation"],
                "pov_character": "Elena",
                "transition_from_previous": "",
                "contrast_with_neighbors": "Slower pace, establishing shots",
            }
        ],
        "rhythm_notes": "This act opens slowly and builds.",
    }

    llm = _mock_llm(response_data)
    agent = ChapterPlanner(llm)
    ctx = AgentContext(
        manuscript_id="test",
        premise="Test",
        extra={"act": {"name": "Act 1", "purpose": "Setup"}},
    )

    result = await agent.execute(ctx)
    assert result.success
    assert len(result.parsed.chapters) == 1
    assert result.parsed.chapters[0].scene_count == 3


@pytest.mark.asyncio
async def test_scene_planner():
    response_data = {
        "scenes": [
            {
                "ordinal": 1,
                "pov_character": "Elena",
                "location": "Ferry dock",
                "time_marker": "Late afternoon, Day 1",
                "purpose": "Establish Elena's return and her unease",
                "conflict": "Internal resistance to returning",
                "stakes": "Emotional exposure",
                "revelation": None,
                "emotional_turn": "Reluctance → resigned commitment",
                "dramatic_function": "establishment",
                "characters_present": ["Elena"],
                "prohibited_moves": ["flashback", "interior monologue dump"],
                "themes_touched": ["isolation"],
                "symbols_touched": ["water"],
                "setup_links": [],
                "payoff_links": ["Elena's reason for leaving"],
                "state_mutations": {"elena_location": "island"},
                "is_pivotal": False,
            }
        ],
    }

    llm = _mock_llm(response_data)
    agent = ScenePlanner(llm)
    ctx = AgentContext(
        manuscript_id="test",
        premise="Test",
        chapter_brief={"title": "Arrival", "scene_count": 1, "scene_summaries": ["Elena arrives"]},
    )

    result = await agent.execute(ctx)
    assert result.success
    assert len(result.parsed.scenes) == 1
    assert result.parsed.scenes[0].location == "Ferry dock"


@pytest.mark.asyncio
async def test_promise_seeder():
    response_data = {
        "promises": [
            {
                "type": "plot",
                "description": "Elena's sister's disappearance must be explained.",
                "salience": 0.95,
                "expected_introduction": "Act 1, Chapter 1",
                "expected_resolution_window": "Act 3, climax",
            },
            {
                "type": "emotional",
                "description": "Elena's guilt about leaving must surface.",
                "salience": 0.8,
                "expected_introduction": "Act 1",
                "expected_resolution_window": "Act 3",
            },
        ],
        "notes": "The plot and emotional promises interlock at the climax.",
    }

    llm = _mock_llm(response_data)
    agent = PromiseSeeder(llm)
    ctx = AgentContext(
        manuscript_id="test",
        premise="Test",
        controlling_design={"central_question": "test"},
        extra={"acts": [{"ordinal": 1, "name": "Act 1"}]},
    )

    result = await agent.execute(ctx)
    assert result.success
    assert len(result.parsed.promises) == 2
    assert result.parsed.promises[0].salience == 0.95
