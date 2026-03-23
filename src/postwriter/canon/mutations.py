"""Canon mutation tracking: extracts state changes from accepted scene prose."""

from __future__ import annotations

import json
import logging
from typing import Any

from postwriter.llm.client import LLMClient
from postwriter.types import ModelTier

logger = logging.getLogger(__name__)


class MutationExtractor:
    """Extracts story state mutations from accepted scene prose using Haiku."""

    def __init__(self, llm: LLMClient) -> None:
        self._llm = llm

    async def extract(
        self,
        prose: str,
        scene_brief: dict[str, Any],
        characters: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """Extract state mutations from accepted prose.

        Returns a dict describing what changed in the story state.
        """
        char_names = [c.get("name", "") for c in characters]

        prompt = (
            f"## Scene Brief\n"
            f"Purpose: {scene_brief.get('purpose', '')}\n"
            f"Characters: {', '.join(char_names)}\n\n"
            f"## Accepted Prose\n{prose[:3000]}\n\n"
            "Extract what changed in the story state after this scene. Return JSON:\n"
            "{\n"
            '  "character_changes": [{"character": str, "emotional_shift": str, '
            '"new_knowledge": [str], "relationship_changes": [str]}],\n'
            '  "plot_developments": [str],\n'
            '  "new_information_revealed": [str],\n'
            '  "promises_touched": [{"description": str, "action": "introduced|developed|resolved"}],\n'
            '  "location_at_end": str,\n'
            '  "time_at_end": str\n'
            "}"
        )

        response = await self._llm.complete(
            tier=ModelTier.HAIKU,
            messages=[{"role": "user", "content": prompt}],
            system="Extract story state changes from this scene prose. Be factual and precise.",
            max_tokens=1024,
            temperature=0.0,
        )

        try:
            text = response.text.strip()
            if text.startswith("```"):
                text = "\n".join(text.split("\n")[1:-1])
            return json.loads(text)
        except (json.JSONDecodeError, Exception) as e:
            logger.warning("Could not parse mutation extraction: %s", e)
            return {"extraction_failed": True, "raw_response": response.text[:500]}
