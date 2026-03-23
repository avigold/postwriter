"""Thematic overstatement audit: detects themes stated rather than dramatised."""

from __future__ import annotations

import json
import logging
from typing import Any

from postwriter.llm.client import LLMClient
from postwriter.revision.base import RevisionProposal
from postwriter.types import ModelTier

logger = logging.getLogger(__name__)


class ThemeOverstatementAudit:
    """Audits for thematic overstatement across the manuscript."""

    name = "theme_overstatement"

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm

    async def audit(self, manuscript_data: dict[str, Any]) -> list[RevisionProposal]:
        proposals: list[RevisionProposal] = []
        themes = manuscript_data.get("themes", [])
        theme_manifestations = manuscript_data.get("theme_manifestations", {})

        for theme in themes:
            theme_name = theme.get("name", "")
            overstatement_risk = theme.get("overstatement_risk", 0.0)
            manifestations = theme_manifestations.get(theme.get("id", ""), [])

            # Check for high-explicitness manifestations
            explicit_count = sum(
                1 for m in manifestations
                if m.get("explicitness", 0) > 0.7
            )

            if explicit_count > 2:
                proposals.append(RevisionProposal(
                    audit_name=self.name,
                    severity=min(0.8, overstatement_risk + 0.2),
                    description=(
                        f"Theme '{theme_name}' is stated too explicitly in "
                        f"{explicit_count} scenes"
                    ),
                    target_scene_ids=[
                        m.get("scene_id", "") for m in manifestations
                        if m.get("explicitness", 0) > 0.7
                    ],
                    proposed_action=(
                        f"Reduce explicit thematic statements about '{theme_name}'. "
                        "Embody the theme through character action, situational irony, "
                        "and detail selection instead of narrator commentary."
                    ),
                    evidence={
                        "theme": theme_name,
                        "explicit_scenes": explicit_count,
                        "total_manifestations": len(manifestations),
                    },
                ))

            # Check for too-regular symbol recurrence
            symbol_scenes = [m.get("scene_id") for m in manifestations if m.get("mode") == "symbolic"]
            if len(symbol_scenes) > 5:
                # Check if they're too evenly spaced (mechanical)
                proposals.append(RevisionProposal(
                    audit_name=self.name,
                    severity=0.4,
                    description=(
                        f"Theme '{theme_name}': symbolic manifestation may be too regular "
                        f"({len(symbol_scenes)} occurrences)"
                    ),
                    proposed_action=(
                        "Vary the mode of thematic embodiment. If symbols are becoming "
                        "predictable, shift to situational or dialogic manifestation."
                    ),
                    evidence={"symbol_count": len(symbol_scenes)},
                ))

        # Optional: LLM-based spot check for meaning-delivery sentences
        if self._llm and manuscript_data.get("sample_prose"):
            llm_proposals = await self._check_meaning_delivery(
                manuscript_data["sample_prose"], themes
            )
            proposals.extend(llm_proposals)

        return proposals

    async def _check_meaning_delivery(
        self,
        sample_prose: list[dict[str, Any]],
        themes: list[dict[str, Any]],
    ) -> list[RevisionProposal]:
        """Check sample scenes for 'meaning delivery' sentences."""
        proposals = []
        theme_names = [t.get("name", "") for t in themes]

        for sample in sample_prose[:5]:  # Check up to 5 samples
            prose = sample.get("prose", "")[:2000]
            scene_id = sample.get("scene_id", "")

            prompt = (
                f"Themes in this novel: {', '.join(theme_names)}\n\n"
                f"Prose:\n{prose}\n\n"
                "Find any sentences where the narrator explicitly STATES a theme rather "
                "than dramatizing it. These are 'meaning delivery' sentences — places where "
                "the text tells the reader what to think instead of showing.\n\n"
                "Respond with JSON: [{sentence: str, theme: str, suggestion: str}]\n"
                "Return empty array if none found."
            )

            try:
                response = await self._llm.complete(
                    tier=ModelTier.HAIKU,
                    messages=[{"role": "user", "content": prompt}],
                    system="Find thematic overstatement in prose. Be precise.",
                    max_tokens=1024,
                    temperature=0.0,
                )
                text = response.text.strip()
                if text.startswith("```"):
                    text = "\n".join(text.split("\n")[1:-1])
                items = json.loads(text)

                for item in items:
                    proposals.append(RevisionProposal(
                        audit_name=self.name,
                        severity=0.5,
                        description=f"Meaning-delivery sentence: '{item.get('sentence', '')[:80]}...'",
                        target_scene_ids=[scene_id],
                        proposed_action=item.get("suggestion", "Remove or dramatize."),
                        evidence={"theme": item.get("theme", ""), "sentence": item.get("sentence", "")},
                    ))
            except Exception as e:
                logger.warning("Theme overstatement LLM check failed: %s", e)

        return proposals
