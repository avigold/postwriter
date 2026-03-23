"""Backward propagation: modifies earlier scenes to support later revelations."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any

from postwriter.llm.client import LLMClient
from postwriter.revision.base import RevisionProposal
from postwriter.types import ModelTier

logger = logging.getLogger(__name__)


@dataclass
class PropagationTask:
    """A single backward propagation task."""

    target_scene_id: str
    target_chapter_id: str
    instruction: str
    reason: str
    risk: float  # 0-1, higher = riskier change
    source_proposal: RevisionProposal | None = None


class BackwardPropagationPlanner:
    """Plans backward propagation: identifies earlier scenes that need modification
    to support later narrative needs.

    This is triggered by revision proposals that identify late-manuscript
    weaknesses rooted in insufficient early preparation.
    """

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm

    async def plan(
        self,
        proposals: list[RevisionProposal],
        manuscript_data: dict[str, Any],
    ) -> list[PropagationTask]:
        """Convert revision proposals into backward propagation tasks.

        Only proposals that benefit from earlier-scene modification get tasks.
        """
        tasks: list[PropagationTask] = []

        for proposal in proposals:
            if proposal.severity < 0.5:
                continue  # Only propagate for significant issues

            backward_tasks = await self._analyze_proposal(proposal, manuscript_data)
            tasks.extend(backward_tasks)

        # Order tasks to minimize cascade: modify later scenes first
        tasks.sort(key=lambda t: self._scene_ordinal(t.target_scene_id, manuscript_data), reverse=True)

        return tasks

    async def _analyze_proposal(
        self,
        proposal: RevisionProposal,
        manuscript_data: dict[str, Any],
    ) -> list[PropagationTask]:
        """Determine if a proposal needs backward propagation and where."""
        tasks = []

        # Promise-related proposals often need backward propagation
        if proposal.audit_name == "promise_audit":
            if "weak payoff" in proposal.description.lower():
                tasks.extend(self._plan_payoff_strengthening(proposal, manuscript_data))
            elif "unresolved" in proposal.description.lower():
                tasks.extend(self._plan_resolution_preparation(proposal, manuscript_data))

        # Arc issues may need earlier emotional groundwork
        if proposal.audit_name == "arc_audit":
            if "emotional jump" in proposal.description.lower():
                tasks.extend(self._plan_emotional_bridging(proposal, manuscript_data))

        # Theme overstatement may be fixable by seeding earlier
        if proposal.audit_name == "theme_overstatement":
            tasks.extend(self._plan_theme_redistribution(proposal, manuscript_data))

        # Use LLM for complex cases
        if not tasks and self._llm and proposal.severity > 0.6:
            llm_tasks = await self._llm_plan(proposal, manuscript_data)
            tasks.extend(llm_tasks)

        return tasks

    def _plan_payoff_strengthening(
        self, proposal: RevisionProposal, data: dict[str, Any]
    ) -> list[PropagationTask]:
        """Strengthen preparation for a weak payoff by seeding earlier scenes."""
        target_scenes = proposal.target_scene_ids
        if not target_scenes:
            return []

        # Find scenes 3-5 scenes before the payoff
        all_scene_ids = data.get("scene_order", [])
        tasks = []
        for target_id in target_scenes:
            if target_id in all_scene_ids:
                idx = all_scene_ids.index(target_id)
                # Seed preparation 3-5 scenes earlier
                for offset in [3, 5]:
                    seed_idx = idx - offset
                    if seed_idx >= 0:
                        tasks.append(PropagationTask(
                            target_scene_id=all_scene_ids[seed_idx],
                            target_chapter_id="",
                            instruction=(
                                f"Add subtle preparation for the payoff in scene {target_id}. "
                                "Seed a detail, glance, or moment that will gain retrospective "
                                "significance. Do not telegraph — plant, don't point."
                            ),
                            reason=f"Strengthening payoff: {proposal.description}",
                            risk=0.3,
                            source_proposal=proposal,
                        ))

        return tasks

    def _plan_resolution_preparation(
        self, proposal: RevisionProposal, data: dict[str, Any]
    ) -> list[PropagationTask]:
        """Prepare for resolving an unresolved promise."""
        all_scene_ids = data.get("scene_order", [])
        if len(all_scene_ids) < 5:
            return []

        # Target the last quarter of the manuscript
        late_start = len(all_scene_ids) * 3 // 4
        return [PropagationTask(
            target_scene_id=all_scene_ids[late_start],
            target_chapter_id="",
            instruction=(
                f"Begin preparing for resolution of: {proposal.description}. "
                "Add a moment of escalation or confrontation that makes resolution "
                "feel imminent and necessary."
            ),
            reason=f"Unresolved promise needs resolution setup",
            risk=0.4,
            source_proposal=proposal,
        )]

    def _plan_emotional_bridging(
        self, proposal: RevisionProposal, data: dict[str, Any]
    ) -> list[PropagationTask]:
        """Bridge an emotional jump by adding transitional beats."""
        target_scenes = proposal.target_scene_ids
        if len(target_scenes) < 2:
            return []

        all_scene_ids = data.get("scene_order", [])
        # Find the scene between the two flagged scenes
        try:
            idx_a = all_scene_ids.index(target_scenes[0])
            idx_b = all_scene_ids.index(target_scenes[1])
            mid_idx = (idx_a + idx_b) // 2
            if mid_idx != idx_a and mid_idx != idx_b:
                return [PropagationTask(
                    target_scene_id=all_scene_ids[mid_idx],
                    target_chapter_id="",
                    instruction=(
                        "Add emotional transitional beats that bridge the shift from "
                        f"{proposal.evidence.get('from', '?')} to {proposal.evidence.get('to', '?')}. "
                        "Show the catalyst or accumulation that makes the shift credible."
                    ),
                    reason=f"Emotional bridging for: {proposal.description}",
                    risk=0.3,
                    source_proposal=proposal,
                )]
        except ValueError:
            pass

        return []

    def _plan_theme_redistribution(
        self, proposal: RevisionProposal, data: dict[str, Any]
    ) -> list[PropagationTask]:
        """Redistribute thematic weight to reduce overstatement."""
        # If theme is overstated in late scenes, reduce it there and seed earlier
        target_scenes = proposal.target_scene_ids
        if not target_scenes:
            return []

        return [PropagationTask(
            target_scene_id=target_scenes[0],
            target_chapter_id="",
            instruction=(
                "Reduce explicit thematic statement in this scene. "
                "Remove or soften narrator commentary about the theme. "
                "Let the situation speak for itself."
            ),
            reason=f"Theme overstatement reduction: {proposal.description}",
            risk=0.2,
            source_proposal=proposal,
        )]

    async def _llm_plan(
        self, proposal: RevisionProposal, data: dict[str, Any]
    ) -> list[PropagationTask]:
        """Use LLM to plan complex backward propagation."""
        if not self._llm:
            return []

        prompt = (
            f"## Revision Proposal\n{proposal.description}\n"
            f"Severity: {proposal.severity}\n"
            f"Target scenes: {proposal.target_scene_ids}\n\n"
            f"## Manuscript has {len(data.get('scene_order', []))} scenes\n\n"
            "Should this be fixed by modifying earlier scenes? If so, which scenes "
            "and what changes? Respond with JSON:\n"
            "[{target_scene_index: int, instruction: str, risk: float}]\n"
            "Return empty array if backward propagation is not needed."
        )

        try:
            response = await self._llm.complete(
                tier=ModelTier.HAIKU,
                messages=[{"role": "user", "content": prompt}],
                system="Plan backward propagation for fiction revision. Be conservative.",
                max_tokens=1024,
                temperature=0.0,
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = "\n".join(text.split("\n")[1:-1])
            items = json.loads(text)

            all_scenes = data.get("scene_order", [])
            tasks = []
            for item in items:
                idx = item.get("target_scene_index", 0)
                if 0 <= idx < len(all_scenes):
                    tasks.append(PropagationTask(
                        target_scene_id=all_scenes[idx],
                        target_chapter_id="",
                        instruction=item.get("instruction", ""),
                        reason=f"LLM-planned propagation for: {proposal.description}",
                        risk=float(item.get("risk", 0.5)),
                        source_proposal=proposal,
                    ))
            return tasks
        except Exception as e:
            logger.warning("LLM backward propagation planning failed: %s", e)
            return []

    @staticmethod
    def _scene_ordinal(scene_id: str, data: dict[str, Any]) -> int:
        scene_order = data.get("scene_order", [])
        try:
            return scene_order.index(scene_id)
        except ValueError:
            return 0
