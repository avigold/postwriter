"""Scene orchestration loop: draft → validate → repair → score → select."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from postwriter.agents.local_rewriter import LocalRewriter
from postwriter.canon.mutations import MutationExtractor
from postwriter.canon.store import CanonStore
from postwriter.cli import display
from postwriter.llm.client import LLMClient
from postwriter.orchestrator.branch_manager import BranchCandidate, BranchManager
from postwriter.orchestrator.policies import ScenePolicy
from postwriter.prompts.loader import PromptLoader
from postwriter.repair.planner import RepairPlanner
from postwriter.scoring.vectors import ScoreVectorData, scores_from_validation
from postwriter.types import AgentContext, BranchStatus, SceneStatus
from postwriter.validation.base import ValidationContext, ValidationSuite

logger = logging.getLogger(__name__)


class SceneLoop:
    """The core inner loop for processing a single scene.

    1. Generate branches
    2. Validate each branch
    3. Score each branch
    4. Select best (or repair and re-score)
    5. Commit accepted draft
    """

    def __init__(
        self,
        session: AsyncSession,
        llm: LLMClient,
        prompts: PromptLoader | None = None,
        policy: ScenePolicy | None = None,
    ) -> None:
        self._session = session
        self._llm = llm
        self._prompts = prompts or PromptLoader()
        self._policy = policy or ScenePolicy()
        self._store = CanonStore(session)
        self._branch_mgr = BranchManager(
            llm, prompts,
            default_count=self._policy.branch_count,
            pivotal_count=self._policy.pivotal_branch_count,
        )
        self._validator = ValidationSuite(llm)
        self._repair_planner = RepairPlanner()
        self._mutation_extractor = MutationExtractor(llm)

    async def process_scene(
        self,
        manuscript_id: uuid.UUID,
        scene_id: uuid.UUID,
        context: AgentContext,
        is_pivotal: bool = False,
    ) -> BranchCandidate | None:
        """Process a single scene through the full loop."""
        # Update status
        await self._store.update_scene_status(
            manuscript_id, scene_id, status=SceneStatus.DRAFTING
        )

        # Step 1: Generate branches
        candidates = await self._branch_mgr.generate_branches(context, is_pivotal)
        if not candidates:
            logger.error("No branches generated for scene %s", scene_id)
            return None

        display.info(f"  Generated {len(candidates)} branch(es)")

        # Step 2: Validate and score each branch
        await self._store.update_scene_status(
            manuscript_id, scene_id, status=SceneStatus.VALIDATING
        )

        for candidate in candidates:
            val_ctx = self._build_validation_context(candidate.prose, context)
            results = await self._validator.run_hard(val_ctx)
            scores = scores_from_validation(results)
            candidate.scores = scores
            candidate.hard_pass = scores.hard_pass

        # Step 3: Select best candidate
        best = BranchManager.select_best(candidates)
        if not best:
            logger.error("No viable candidates for scene %s", scene_id)
            return None

        # Step 4: Repair loop if needed
        if not best.hard_pass or (best.scores and best.scores.composite < self._policy.acceptance_threshold):
            await self._store.update_scene_status(
                manuscript_id, scene_id, status=SceneStatus.REPAIRING
            )
            best = await self._repair_loop(manuscript_id, scene_id, best, context)

        # Step 5: Commit the accepted draft
        draft = await self._store.create_draft(
            manuscript_id,
            scene_id=scene_id,
            branch_label=best.label,
            prose=best.prose,
            branch_status=BranchStatus.SELECTED,
        )
        await self._store.update_scene_status(
            manuscript_id, scene_id,
            status=SceneStatus.ACCEPTED,
            accepted_draft_id=draft.id,
        )

        # Store other branches as pruned
        for candidate in candidates:
            if candidate is not best:
                await self._store.create_draft(
                    manuscript_id,
                    scene_id=scene_id,
                    branch_label=candidate.label,
                    prose=candidate.prose,
                    branch_status=BranchStatus.PRUNED,
                )

        # Step 6: Extract state mutations
        mutations = await self._mutation_extractor.extract(
            best.prose,
            context.scene_brief,
            context.characters,
        )
        await self._store.update_scene_status(
            manuscript_id, scene_id, state_mutations=mutations
        )

        await self._session.flush()
        display.success(
            f"  Accepted: {best.label} "
            f"({best.word_count} words, "
            f"score={best.scores.composite:.2f})" if best.scores else f"  Accepted: {best.label}"
        )

        return best

    async def _repair_loop(
        self,
        manuscript_id: uuid.UUID,
        scene_id: uuid.UUID,
        candidate: BranchCandidate,
        context: AgentContext,
    ) -> BranchCandidate:
        """Run the repair loop on a candidate until it passes or budget is exhausted."""
        prev_score = candidate.scores.composite if candidate.scores else 0.0
        best_so_far = candidate

        for round_num in range(self._policy.max_repair_rounds):
            # Get validation results for repair planning
            val_ctx = self._build_validation_context(candidate.prose, context)
            hard_results = await self._validator.run_hard(val_ctx)

            # Plan repairs
            repair_actions = self._repair_planner.plan(hard_results)
            if not repair_actions:
                break

            display.info(
                f"  Repair round {round_num + 1}: {len(repair_actions)} action(s)"
            )

            # Apply repairs via local rewriter
            rewriter = LocalRewriter(
                self._llm, self._prompts, repair_actions=repair_actions
            )
            repair_context = AgentContext(
                manuscript_id=str(manuscript_id),
                scene_brief=context.scene_brief,
                style_profile=context.style_profile,
                extra={"current_prose": candidate.prose},
            )
            result = await rewriter.execute(repair_context)

            if not result.success or not result.raw_response:
                break

            # Re-validate
            candidate = BranchCandidate(f"{candidate.label}_r{round_num + 1}", result.raw_response)
            val_ctx = self._build_validation_context(candidate.prose, context)
            hard_results = await self._validator.run_hard(val_ctx)
            scores = scores_from_validation(hard_results)
            candidate.scores = scores
            candidate.hard_pass = scores.hard_pass

            # Track best
            if scores.composite > (best_so_far.scores.composite if best_so_far.scores else 0):
                best_so_far = candidate

            # Check convergence
            if scores.hard_pass and scores.composite >= self._policy.acceptance_threshold:
                return candidate

            delta = scores.composite - prev_score
            if delta < self._policy.min_improvement_delta:
                display.info(f"  Repair converged (delta={delta:.3f})")
                break

            prev_score = scores.composite

        return best_so_far

    def _build_validation_context(
        self, prose: str, agent_ctx: AgentContext
    ) -> ValidationContext:
        return ValidationContext(
            prose=prose,
            scene_brief=agent_ctx.scene_brief,
            chapter_brief=agent_ctx.chapter_brief,
            characters=agent_ctx.characters,
            character_states=agent_ctx.character_states,
            preceding_scenes=agent_ctx.preceding_scenes,
            open_promises=agent_ctx.open_promises,
            style_profile=agent_ctx.style_profile,
            manuscript_id=agent_ctx.manuscript_id,
        )
