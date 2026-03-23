"""Context condenser: produces agent-specific summaries from full context files.

Each planning agent needs different aspects of the user's context.
The character designer doesn't need the style guide; the style builder
doesn't need the plot outline. This module runs a cheap Haiku call
to produce focused summaries, keeping total prompt size manageable.
"""

from __future__ import annotations

import logging
from typing import Any

from postwriter.context.loader import ContextFile, ContextType
from postwriter.llm.client import LLMClient
from postwriter.types import ModelTier

logger = logging.getLogger(__name__)

# What each agent role needs from context
AGENT_CONTEXT_NEEDS: dict[str, set[ContextType]] = {
    "premise_architect": {ContextType.PLOT, ContextType.CHARACTERS, ContextType.WORLD, ContextType.GUIDELINES},
    "spine_architect": {ContextType.PLOT, ContextType.GUIDELINES},
    "character_designer": {ContextType.CHARACTERS, ContextType.PLOT},
    "style_builder": {ContextType.STYLE, ContextType.SAMPLE_WRITING},
    "chapter_planner": {ContextType.PLOT, ContextType.GUIDELINES},
    "scene_planner": {ContextType.PLOT},
    "promise_seeder": {ContextType.PLOT, ContextType.CHARACTERS},
}

# Max chars per context file after condensation
MAX_CONDENSED_CHARS = 1500


class ContextCondenser:
    """Produces agent-specific condensed context from full context files."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm
        self._cache: dict[str, list[dict[str, Any]]] = {}

    def filter_for_agent(
        self,
        agent_role: str,
        context_files: list[ContextFile],
    ) -> list[dict[str, Any]]:
        """Return only the context files relevant to a specific agent role.

        Files are included based on their type matching the agent's needs.
        Files that don't match are excluded entirely. Files that are already
        short enough are passed through unchanged.
        """
        needs = AGENT_CONTEXT_NEEDS.get(agent_role)
        if needs is None:
            # Unknown agent — give everything but truncate
            return self._truncate_all(context_files)

        relevant = [f for f in context_files if f.context_type in needs and not f.is_image]

        result = []
        for f in relevant:
            entry = {
                "name": f.name,
                "type": f.context_type.value,
                "content": f.content if len(f.content) <= MAX_CONDENSED_CHARS else f.content[:MAX_CONDENSED_CHARS] + "\n\n[truncated]",
            }
            result.append(entry)

        return result

    async def condense_for_agent(
        self,
        agent_role: str,
        context_files: list[ContextFile],
    ) -> list[dict[str, Any]]:
        """Condense context files for a specific agent using Haiku.

        Falls back to filter_for_agent if no LLM is available.
        Results are cached per agent role.
        """
        if agent_role in self._cache:
            return self._cache[agent_role]

        if not self._llm:
            result = self.filter_for_agent(agent_role, context_files)
            self._cache[agent_role] = result
            return result

        needs = AGENT_CONTEXT_NEEDS.get(agent_role)
        if needs is None:
            result = self._truncate_all(context_files)
            self._cache[agent_role] = result
            return result

        relevant = [f for f in context_files if f.context_type in needs and not f.is_image]

        result = []
        for f in relevant:
            if len(f.content) <= MAX_CONDENSED_CHARS:
                result.append({
                    "name": f.name,
                    "type": f.context_type.value,
                    "content": f.content,
                })
            else:
                condensed = await self._condense_file(f, agent_role)
                result.append({
                    "name": f.name,
                    "type": f.context_type.value,
                    "content": condensed,
                })

        self._cache[agent_role] = result
        return result

    async def _condense_file(self, f: ContextFile, agent_role: str) -> str:
        """Use Haiku to condense a single context file for a specific agent."""
        role_focus = {
            "character_designer": "character details, relationships, and psychological traits",
            "style_builder": "voice, tone, prose style, and banned phrases",
            "premise_architect": "plot premise, setting, and thematic direction",
            "spine_architect": "plot structure and narrative arc",
            "chapter_planner": "plot progression and chapter-level structure",
            "scene_planner": "scene-level plot beats",
            "promise_seeder": "narrative promises, setups, and payoff obligations",
        }
        focus = role_focus.get(agent_role, "key details")

        try:
            response = await self._llm.complete(
                tier=ModelTier.HAIKU,
                messages=[{
                    "role": "user",
                    "content": (
                        f"Condense the following reference document to its essential details, "
                        f"focusing on {focus}. Preserve specific names, traits, and constraints. "
                        f"Remove generic advice and redundant elaboration. "
                        f"Keep it under {MAX_CONDENSED_CHARS} characters.\n\n"
                        f"---\n{f.content}\n---"
                    ),
                }],
                system="You are a concise summariser. Preserve specifics. Cut filler.",
                max_tokens=1024,
                temperature=0.0,
            )
            condensed = response.text.strip()
            logger.debug(
                "Condensed %s for %s: %d -> %d chars",
                f.name, agent_role, len(f.content), len(condensed),
            )
            return condensed
        except Exception as e:
            logger.warning("Failed to condense %s: %s, using truncation", f.name, e)
            return f.content[:MAX_CONDENSED_CHARS] + "\n\n[truncated]"

    @staticmethod
    def _truncate_all(context_files: list[ContextFile]) -> list[dict[str, Any]]:
        return [
            {
                "name": f.name,
                "type": f.context_type.value,
                "content": f.content[:MAX_CONDENSED_CHARS] + ("\n\n[truncated]" if len(f.content) > MAX_CONDENSED_CHARS else ""),
            }
            for f in context_files
            if not f.is_image
        ]
