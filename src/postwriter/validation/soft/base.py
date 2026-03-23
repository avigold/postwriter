"""Base class for soft critics with common LLM evaluation pattern."""

from __future__ import annotations

import json
import logging
from typing import Any

from postwriter.llm.client import LLMClient
from postwriter.types import ModelTier, ValidationResult
from postwriter.validation.base import BaseValidator, ValidationContext

logger = logging.getLogger(__name__)


class BaseSoftCritic(BaseValidator):
    """Base for all soft critics. Sends prose + context to Sonnet, expects JSON response.

    Subclasses set:
        - name: str
        - dimension: str (which score vector dimension this maps to)
        - system_prompt: str
        - evaluation_prompt_template: str (with {prose}, {scene_brief} placeholders)
    """

    is_hard = False
    dimension: str = ""
    system_prompt: str = ""
    evaluation_prompt_template: str = ""

    async def validate(self, ctx: ValidationContext) -> ValidationResult:
        if not self._llm:
            return ValidationResult(
                validator_name=self.name, is_hard=False, passed=None,
                score=0.5, diagnosis="No LLM available.",
            )

        prompt = self._build_prompt(ctx)

        try:
            response = await self._llm.complete(
                tier=ModelTier.SONNET,
                messages=[{"role": "user", "content": prompt}],
                system=self.system_prompt,
                max_tokens=1024,
                temperature=0.0,
            )

            result = self._parse_response(response.text)
            return ValidationResult(
                validator_name=self.name,
                is_hard=False,
                passed=None,
                score=result.get("score", 0.5),
                diagnosis=result.get("diagnosis", ""),
                repair_opportunities=result.get("repair_opportunities", []),
                confidence=result.get("confidence", 0.7),
            )

        except Exception as e:
            logger.warning("Soft critic %s failed: %s", self.name, e)
            return ValidationResult(
                validator_name=self.name, is_hard=False, passed=None,
                score=0.5, diagnosis=f"Critic error: {e}",
            )

    def _build_prompt(self, ctx: ValidationContext) -> str:
        parts = []

        parts.append(f"## Scene Brief\nPurpose: {ctx.scene_brief.get('purpose', '')}")
        parts.append(f"Conflict: {ctx.scene_brief.get('conflict', '')}")
        parts.append(f"Emotional Turn: {ctx.scene_brief.get('emotional_turn', '')}")
        parts.append(f"Stakes: {ctx.scene_brief.get('stakes', '')}")

        if ctx.characters:
            parts.append("\n## Characters")
            for c in ctx.characters[:5]:
                parts.append(f"- {c.get('name', '?')}: {c.get('biography', '')[:100]}")

        parts.append(f"\n## Prose ({len(ctx.prose.split())} words)\n\n{ctx.prose[:4000]}")

        parts.append(self._extra_context(ctx))

        parts.append(
            "\n## Evaluation Task\n"
            f"{self.evaluation_prompt_template}\n\n"
            "Respond with JSON:\n"
            "{\n"
            '  "score": float (0.0-1.0),\n'
            '  "diagnosis": str (2-3 sentences explaining the score),\n'
            '  "repair_opportunities": [str] (specific, actionable improvements),\n'
            '  "confidence": float (0.0-1.0, how confident you are in this assessment)\n'
            "}"
        )

        return "\n".join(parts)

    def _extra_context(self, ctx: ValidationContext) -> str:
        """Override to add critic-specific context."""
        return ""

    @staticmethod
    def _parse_response(text: str) -> dict[str, Any]:
        text = text.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            text = "\n".join(lines[1:-1]) if len(lines) > 2 else text
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            return {"score": 0.5, "diagnosis": "Could not parse critic response."}
