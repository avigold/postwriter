"""Character arc audit: detects emotional jumps, unearned transformations, and contradictions."""

from __future__ import annotations

import json
import logging
from typing import Any

from postwriter.llm.client import LLMClient
from postwriter.revision.base import RevisionProposal
from postwriter.types import ModelTier

logger = logging.getLogger(__name__)


class ArcAudit:
    """Audits character arcs for credibility and consistency."""

    name = "arc_audit"

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm

    async def audit(self, manuscript_data: dict[str, Any]) -> list[RevisionProposal]:
        proposals: list[RevisionProposal] = []
        characters = manuscript_data.get("characters", [])
        scene_states = manuscript_data.get("scene_states", {})

        for char in characters:
            char_name = char.get("name", "Unknown")
            char_id = char.get("id", "")
            states = scene_states.get(char_id, [])

            if len(states) < 2:
                continue

            # Check for emotional jumps between adjacent scenes
            for i in range(len(states) - 1):
                current = states[i]
                next_state = states[i + 1]

                current_emotion = current.get("emotional_state", {})
                next_emotion = next_state.get("emotional_state", {})

                # Simple heuristic: if emotional descriptors are completely different
                # with no transition scene, flag it
                if current_emotion and next_emotion:
                    current_desc = str(current_emotion).lower()
                    next_desc = str(next_emotion).lower()

                    # Check for dramatic polarity shifts
                    positive = {"happy", "hopeful", "calm", "content", "relief", "joy"}
                    negative = {"angry", "grief", "despair", "fear", "rage", "guilt"}

                    curr_pos = any(w in current_desc for w in positive)
                    curr_neg = any(w in current_desc for w in negative)
                    next_pos = any(w in next_desc for w in positive)
                    next_neg = any(w in next_desc for w in negative)

                    if (curr_pos and next_neg) or (curr_neg and next_pos):
                        proposals.append(RevisionProposal(
                            audit_name=self.name,
                            severity=0.6,
                            description=(
                                f"{char_name}: emotional jump from "
                                f"{current_emotion} to {next_emotion} "
                                f"between scenes {current.get('scene_id')} and {next_state.get('scene_id')}"
                            ),
                            target_scene_ids=[
                                current.get("scene_id", ""),
                                next_state.get("scene_id", ""),
                            ],
                            proposed_action=(
                                "Add transitional emotional beats or show the catalyst "
                                "for this emotional shift more clearly."
                            ),
                            evidence={
                                "character": char_name,
                                "from": current_emotion,
                                "to": next_emotion,
                            },
                        ))

            # Check arc hypothesis vs realized arc
            arc_hypothesis = char.get("arc_hypotheses", {}).get("hypothesis", "")
            if arc_hypothesis and self._llm and len(states) > 3:
                arc_proposal = await self._check_arc_completion(
                    char_name, arc_hypothesis, states
                )
                if arc_proposal:
                    proposals.append(arc_proposal)

        return proposals

    async def _check_arc_completion(
        self,
        char_name: str,
        hypothesis: str,
        states: list[dict[str, Any]],
    ) -> RevisionProposal | None:
        """Use LLM to check if the arc hypothesis is being fulfilled."""
        state_summary = "\n".join(
            f"Scene {s.get('scene_id', '?')}: emotion={s.get('emotional_state', '?')}, "
            f"knowledge={s.get('knowledge_state', '?')}"
            for s in states[-10:]  # Last 10 states
        )

        prompt = (
            f"Character: {char_name}\n"
            f"Arc Hypothesis: {hypothesis}\n\n"
            f"Recent Scene States:\n{state_summary}\n\n"
            "Does this character's arc progression support the hypothesis? "
            "Respond with JSON: {supported: bool, gap: str, suggestion: str}"
        )

        try:
            response = await self._llm.complete(
                tier=ModelTier.HAIKU,
                messages=[{"role": "user", "content": prompt}],
                system="Evaluate character arc progression. Be concise.",
                max_tokens=512,
                temperature=0.0,
            )
            text = response.text.strip()
            if text.startswith("```"):
                text = "\n".join(text.split("\n")[1:-1])
            data = json.loads(text)

            if not data.get("supported", True):
                return RevisionProposal(
                    audit_name=self.name,
                    severity=0.5,
                    description=f"{char_name}: arc may not fulfill hypothesis. {data.get('gap', '')}",
                    proposed_action=data.get("suggestion", "Review character arc."),
                    requires_human_approval=True,
                    evidence={"hypothesis": hypothesis, "gap": data.get("gap", "")},
                )
        except Exception as e:
            logger.warning("Arc completion check failed for %s: %s", char_name, e)

        return None
