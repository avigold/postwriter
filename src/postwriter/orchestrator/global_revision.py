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

        display.success(
            f"Global revision complete: {len(all_proposals)} proposals, "
            f"{len(propagation_tasks)} backward propagation tasks"
        )

        return all_proposals

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
