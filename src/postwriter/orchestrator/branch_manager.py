"""Branch manager: generates, evaluates, and selects scene drafts."""

from __future__ import annotations

import asyncio
import logging
from typing import Any

from postwriter.agents.branch_profiles import BranchProfile, get_branch_profiles
from postwriter.agents.scene_writer import SceneWriter
from postwriter.llm.client import LLMClient
from postwriter.prompts.loader import PromptLoader
from postwriter.scoring.vectors import ScoreVectorData
from postwriter.types import AgentContext

logger = logging.getLogger(__name__)


class BranchCandidate:
    """A single branch draft with its scores."""

    __slots__ = ("label", "prose", "word_count", "scores", "hard_pass")

    def __init__(self, label: str, prose: str) -> None:
        self.label = label
        self.prose = prose
        self.word_count = len(prose.split())
        self.scores: ScoreVectorData | None = None
        self.hard_pass = True


class BranchManager:
    """Manages branch generation and selection for a scene."""

    def __init__(
        self,
        llm: LLMClient,
        prompts: PromptLoader | None = None,
        default_count: int = 3,
        pivotal_count: int = 5,
    ) -> None:
        self._llm = llm
        self._prompts = prompts or PromptLoader()
        self._default_count = default_count
        self._pivotal_count = pivotal_count

    async def generate_branches(
        self,
        context: AgentContext,
        is_pivotal: bool = False,
    ) -> list[BranchCandidate]:
        """Generate multiple branch drafts for a scene in parallel."""
        count = self._pivotal_count if is_pivotal else self._default_count
        profiles = get_branch_profiles(count=count, is_pivotal=is_pivotal)

        tasks = [
            self._draft_branch(context, profile)
            for profile in profiles
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        candidates = []
        for profile, result in zip(profiles, results):
            if isinstance(result, Exception):
                logger.error("Branch %s failed: %s", profile.label, result)
                continue
            if result:
                candidates.append(result)

        if not candidates:
            # Fallback: try a single default branch
            logger.warning("All branches failed, attempting fallback")
            writer = SceneWriter(self._llm, self._prompts)
            agent_result = await writer.execute(context)
            if agent_result.success and agent_result.raw_response:
                candidates.append(BranchCandidate("fallback", agent_result.raw_response))

        return candidates

    async def _draft_branch(
        self, context: AgentContext, profile: BranchProfile
    ) -> BranchCandidate | None:
        writer = SceneWriter(self._llm, self._prompts, branch_profile=profile)
        result = await writer.execute(context)

        if result.success and result.raw_response:
            return BranchCandidate(profile.label, result.raw_response)
        return None

    @staticmethod
    def select_best(candidates: list[BranchCandidate]) -> BranchCandidate | None:
        """Select the best candidate based on scores.

        Selection criteria (in order):
        1. Must pass hard validation
        2. Highest composite score
        """
        passing = [c for c in candidates if c.hard_pass]
        if not passing:
            # If none pass hard validation, return the one with fewest issues
            # (they'll go through repair)
            return candidates[0] if candidates else None

        # Sort by composite score (highest first)
        passing.sort(
            key=lambda c: c.scores.composite if c.scores else 0.0,
            reverse=True,
        )
        return passing[0]
