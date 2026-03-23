"""Tests for the branch manager."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from postwriter.llm.budget import TokenBudget
from postwriter.llm.client import LLMClient, LLMResponse
from postwriter.orchestrator.branch_manager import BranchCandidate, BranchManager
from postwriter.scoring.vectors import ScoreVectorData
from postwriter.types import AgentContext


def _make_mock_llm(prose: str = "Test prose for branch.") -> LLMClient:
    client = MagicMock(spec=LLMClient)
    client.complete = AsyncMock(
        return_value=LLMResponse(
            text=prose,
            tool_use=[],
            input_tokens=300,
            output_tokens=200,
            model="claude-sonnet-4-6",
            stop_reason="end_turn",
        )
    )
    client.budget = TokenBudget()
    return client


@pytest.mark.asyncio
async def test_generate_branches():
    llm = _make_mock_llm("The harbor stretched before her, gray and indifferent.")
    mgr = BranchManager(llm, default_count=3)
    ctx = AgentContext(manuscript_id="test", scene_brief={"purpose": "arrival"})

    branches = await mgr.generate_branches(ctx)
    assert len(branches) == 3
    assert all(b.prose for b in branches)
    assert all(b.word_count > 0 for b in branches)


@pytest.mark.asyncio
async def test_generate_pivotal_branches():
    llm = _make_mock_llm("Test pivotal scene prose.")
    mgr = BranchManager(llm, pivotal_count=5)
    ctx = AgentContext(manuscript_id="test", scene_brief={"purpose": "climax"})

    branches = await mgr.generate_branches(ctx, is_pivotal=True)
    assert len(branches) == 5


def test_select_best_by_composite():
    candidates = []
    for i, (label, score) in enumerate([
        ("sparse", 0.6),
        ("lyrical", 0.8),
        ("restrained", 0.7),
    ]):
        c = BranchCandidate(label, f"Prose for {label}")
        c.scores = ScoreVectorData(composite=score)
        c.hard_pass = True
        candidates.append(c)

    best = BranchManager.select_best(candidates)
    assert best is not None
    assert best.label == "lyrical"


def test_select_best_prefers_hard_pass():
    c1 = BranchCandidate("failing", "Bad prose")
    c1.scores = ScoreVectorData(composite=0.9)
    c1.hard_pass = False

    c2 = BranchCandidate("passing", "Good prose")
    c2.scores = ScoreVectorData(composite=0.5)
    c2.hard_pass = True

    best = BranchManager.select_best([c1, c2])
    assert best is not None
    assert best.label == "passing"  # Lower score but passes hard validation


def test_select_best_no_candidates():
    best = BranchManager.select_best([])
    assert best is None


def test_select_best_all_failing():
    c1 = BranchCandidate("a", "Prose A")
    c1.hard_pass = False
    c1.scores = ScoreVectorData(composite=0.3)

    c2 = BranchCandidate("b", "Prose B")
    c2.hard_pass = False
    c2.scores = ScoreVectorData(composite=0.4)

    # When all fail hard, returns first (they'll go through repair)
    best = BranchManager.select_best([c1, c2])
    assert best is not None
