"""Global revision orchestrator: runs all audit passes and executes revisions."""

from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from postwriter.canon.store import CanonStore
from postwriter.cli import display
from postwriter.llm.client import LLMClient
from postwriter.revision.arc_audit import ArcAudit
from postwriter.revision.backward_propagation import BackwardPropagationPlanner, PropagationTask
from postwriter.revision.base import RevisionProposal
from postwriter.revision.device_ecology import DeviceEcologyAudit
from postwriter.revision.promise_audit import PromiseAudit
from postwriter.revision.rhythm_audit import RhythmAudit
from postwriter.revision.theme_overstatement import ThemeOverstatementAudit

logger = logging.getLogger(__name__)


class GlobalRevisionOrchestrator:
    """Runs all manuscript-level audit passes and coordinates revisions.

    Flow:
    1. Gather manuscript data
    2. Run all audit passes in parallel
    3. Collect and prioritize proposals
    4. Plan backward propagation for high-severity proposals
    5. Present proposals to user at human checkpoint
    6. Execute approved revisions
    """

    def __init__(
        self,
        session: AsyncSession,
        llm: LLMClient,
    ) -> None:
        self._session = session
        self._llm = llm
        self._store = CanonStore(session)

        # Initialize audit passes
        self._audits = [
            PromiseAudit(),
            ArcAudit(llm),
            DeviceEcologyAudit(),
            RhythmAudit(),
            ThemeOverstatementAudit(llm),
        ]
        self._propagation_planner = BackwardPropagationPlanner(llm)

    async def run(self, manuscript_id: uuid.UUID) -> list[RevisionProposal]:
        """Run the full global revision process."""
        display.section("Global Revision")

        # Step 1: Gather manuscript data
        display.info("Gathering manuscript data...")
        manuscript_data = await self._gather_data(manuscript_id)

        # Step 2: Run all audits
        display.info("Running audit passes...")
        all_proposals: list[RevisionProposal] = []
        for audit in self._audits:
            try:
                proposals = await audit.audit(manuscript_data)
                all_proposals.extend(proposals)
                if proposals:
                    display.info(f"  {audit.name}: {len(proposals)} proposal(s)")
            except Exception as e:
                logger.error("Audit %s failed: %s", audit.name, e)

        if not all_proposals:
            display.success("No revision proposals — manuscript looks clean.")
            return []

        # Step 3: Sort by severity
        all_proposals.sort(key=lambda p: p.severity, reverse=True)

        # Step 4: Plan backward propagation
        high_severity = [p for p in all_proposals if p.severity > 0.5]
        propagation_tasks: list[PropagationTask] = []
        if high_severity:
            display.info("Planning backward propagation...")
            propagation_tasks = await self._propagation_planner.plan(
                high_severity, manuscript_data
            )
            if propagation_tasks:
                display.info(f"  {len(propagation_tasks)} backward propagation task(s)")

        # Step 5: Present to user
        display.section("Revision Proposals")
        self._display_proposals(all_proposals, propagation_tasks)

        # HUMAN CHECKPOINT: Approve revisions
        if any(p.requires_human_approval for p in all_proposals) or propagation_tasks:
            if not display.confirm("Proceed with revisions?"):
                display.warning("Revisions skipped by user.")
                return all_proposals

        # Step 6: Execute revisions
        if propagation_tasks:
            display.section("Executing Revisions")
            revised_count = await self._execute_revisions(
                manuscript_id, propagation_tasks, manuscript_data
            )
            display.success(f"Revised {revised_count} scene(s)")

        display.success(
            f"Global revision complete: {len(all_proposals)} proposals, "
            f"{len(propagation_tasks)} backward propagation tasks"
        )

        return all_proposals

    async def _execute_revisions(
        self,
        manuscript_id: uuid.UUID,
        tasks: list[PropagationTask],
        manuscript_data: dict[str, Any],
    ) -> int:
        """Execute backward propagation tasks by rewriting affected scenes."""
        from postwriter.agents.local_rewriter import LocalRewriter
        from postwriter.models.core import Scene, SceneDraft
        from postwriter.prompts.loader import PromptLoader
        from postwriter.repair.actions import RepairActionSpec
        from postwriter.types import BranchStatus, RepairPriority

        revised = 0
        # Deduplicate by scene — multiple tasks may target the same scene
        scene_tasks: dict[str, list[PropagationTask]] = {}
        for task in tasks:
            scene_tasks.setdefault(task.target_scene_id, []).append(task)

        for scene_id_str, scene_revision_tasks in scene_tasks.items():
            scene_id = uuid.UUID(scene_id_str)
            scene = await self._session.get(Scene, scene_id)
            if not scene or not scene.accepted_draft_id:
                continue

            # Get current accepted draft
            draft = await self._session.get(SceneDraft, scene.accepted_draft_id)
            if not draft:
                continue

            # Build repair actions from propagation tasks
            repair_actions = [
                RepairActionSpec(
                    priority=RepairPriority.SETUP_PAYOFF,
                    target_dimension="backward_propagation",
                    instruction=task.instruction,
                    preserve_constraints=["voice", "continuity", "scene_purpose"],
                    issue_diagnosis=task.reason,
                )
                for task in scene_revision_tasks
            ]

            # Get scene context for the rewriter
            from postwriter.canon.slicer import CanonSlicer
            slicer = CanonSlicer(self._session)
            context = await slicer.build_scene_context(manuscript_id, scene_id)

            # Run the rewriter
            display.info(f"  Revising scene {scene_id_str[:8]}... ({len(repair_actions)} action(s))")
            rewriter = LocalRewriter(
                self._llm, PromptLoader(), repair_actions=repair_actions
            )
            context.extra["current_prose"] = draft.prose
            result = await rewriter.execute(context)

            if result.success and result.raw_response and len(result.raw_response) > 100:
                # Save as a new version, preserve original
                new_draft = SceneDraft(
                    scene_id=scene_id,
                    branch_label=f"{draft.branch_label}_revised",
                    version=draft.version + 1,
                    prose=result.raw_response,
                    word_count=len(result.raw_response.split()),
                    branch_status=BranchStatus.SELECTED,
                )
                self._session.add(new_draft)

                # Demote old draft to pruned (but don't delete)
                draft.branch_status = BranchStatus.PRUNED

                await self._session.flush()

                # Update scene to point to new draft
                scene.accepted_draft_id = new_draft.id
                await self._session.flush()
                await self._session.commit()

                revised += 1
                display.success(f"    Revised ({new_draft.word_count} words)")
            else:
                display.warning(f"    Skipped — rewriter produced no usable output")

        return revised

    async def _gather_data(self, manuscript_id: uuid.UUID) -> dict[str, Any]:
        """Gather all manuscript data needed by audit passes."""
        manuscript = await self._store.get_manuscript(manuscript_id)
        if not manuscript:
            return {}

        promises = await self._store.get_promises(manuscript_id)
        characters = await self._store.get_characters(manuscript_id)
        themes = await self._store.get_themes(manuscript_id)
        chapters = await self._store.get_all_chapters(manuscript_id)

        # Build scene order
        scene_order: list[str] = []
        for ch in chapters:
            scenes = await self._store.get_scenes(ch.id)
            for s in scenes:
                scene_order.append(str(s.id))

        # Build character scene states
        scene_states: dict[str, list[dict[str, Any]]] = {}
        for char in characters:
            states = []
            for sid in scene_order:
                char_states = await self._store.get_character_states_for_scene(uuid.UUID(sid))
                for cs in char_states:
                    if str(cs.character_id) == str(char.id):
                        states.append({
                            "scene_id": sid,
                            "emotional_state": cs.emotional_state,
                            "knowledge_state": cs.knowledge_state,
                        })
            scene_states[str(char.id)] = states

        return {
            "manuscript_id": str(manuscript_id),
            "promises": [
                {
                    "id": str(p.id),
                    "description": p.description,
                    "status": p.status.value,
                    "salience": p.salience,
                    "payoff_strength": p.payoff_strength,
                    "resolution_scene_id": str(p.resolution_scene_id) if p.resolution_scene_id else None,
                }
                for p in promises
            ],
            "characters": [
                {
                    "id": str(c.id),
                    "name": c.name,
                    "arc_hypotheses": c.arc_hypotheses,
                }
                for c in characters
            ],
            "themes": [
                {
                    "id": str(t.id),
                    "name": t.name,
                    "overstatement_risk": t.overstatement_risk,
                }
                for t in themes
            ],
            "total_chapters": len(chapters),
            "scene_order": scene_order,
            "scene_states": scene_states,
            "chapter_rhythms": [],  # Populated later from device analysis
            "chapter_devices": {},
        }

    @staticmethod
    def _display_proposals(
        proposals: list[RevisionProposal],
        propagation_tasks: list[PropagationTask],
    ) -> None:
        for i, p in enumerate(proposals[:10]):  # Show top 10
            severity_label = "HIGH" if p.severity > 0.7 else "MED" if p.severity > 0.4 else "LOW"
            human = " [NEEDS APPROVAL]" if p.requires_human_approval else ""
            display.info(
                f"  [{severity_label}] {p.audit_name}: {p.description}{human}"
            )
            if p.proposed_action:
                display.info(f"        Action: {p.proposed_action[:100]}")

        if len(proposals) > 10:
            display.info(f"  ... and {len(proposals) - 10} more")

        if propagation_tasks:
            display.info("")
            display.info(f"  Backward propagation: {len(propagation_tasks)} scene(s) to modify")
            for t in propagation_tasks[:5]:
                display.info(f"    Scene {t.target_scene_id[:8]}...: {t.instruction[:80]}")
