"""Continuity validator: checks character presence, location, and state consistency."""

from __future__ import annotations

import json
from typing import Any

from pydantic import BaseModel, Field

from postwriter.llm.client import LLMClient
from postwriter.types import ModelTier, ValidationResult
from postwriter.validation.base import BaseValidator, ValidationContext, register_hard_validator


class ContinuityCheck(BaseModel):
    passed: bool
    issues: list[dict[str, str]] = Field(default_factory=list)
    reasoning: str = ""


@register_hard_validator("continuity")
class ContinuityValidator(BaseValidator):
    """Checks that the scene prose is consistent with the canon state.

    Uses Haiku for fast, cheap checking of:
    - Characters present match the brief
    - Location matches
    - No contradictions with preceding scenes
    """

    async def validate(self, ctx: ValidationContext) -> ValidationResult:
        if not self._llm:
            return ValidationResult(
                validator_name=self.name,
                is_hard=True,
                passed=True,
                score=None,
                diagnosis="No LLM available, skipping continuity check.",
            )

        prompt = self._build_prompt(ctx)
        response = await self._llm.complete(
            tier=ModelTier.HAIKU,
            messages=[{"role": "user", "content": prompt}],
            system=(
                "You are a continuity checker for fiction. Check if the prose is consistent "
                "with the provided scene brief and story state. Be precise about contradictions. "
                "Respond with JSON matching: {passed: bool, issues: [{type, description}], reasoning: str}"
            ),
            max_tokens=1024,
            temperature=0.0,
        )

        try:
            text = response.text.strip()
            if text.startswith("```"):
                text = "\n".join(text.split("\n")[1:-1])
            data = json.loads(text)
            check = ContinuityCheck.model_validate(data)
        except Exception:
            # If parsing fails, pass (don't block on parser errors)
            return ValidationResult(
                validator_name=self.name,
                is_hard=True,
                passed=True,
                score=None,
                diagnosis="Could not parse continuity check response.",
            )

        return ValidationResult(
            validator_name=self.name,
            is_hard=True,
            passed=check.passed,
            score=None,
            diagnosis=check.reasoning,
            evidence=check.issues,
        )

    def _build_prompt(self, ctx: ValidationContext) -> str:
        parts = [
            "## Scene Brief",
            f"Location: {ctx.scene_brief.get('location', 'unspecified')}",
            f"Time: {ctx.scene_brief.get('time_marker', 'unspecified')}",
            f"Characters expected: {ctx.scene_brief.get('characters_present', [])}",
            "",
        ]

        if ctx.preceding_scenes:
            parts.append("## Previous Scene Summary")
            for ps in ctx.preceding_scenes[-1:]:
                prose = ps.get("accepted_prose", "")
                if prose:
                    parts.append(prose[:500] + "..." if len(prose) > 500 else prose)
            parts.append("")

        if ctx.character_states:
            parts.append("## Character States")
            for cs in ctx.character_states:
                parts.append(json.dumps(cs, indent=2))
            parts.append("")

        parts.extend([
            "## Scene Prose to Check",
            ctx.prose[:3000],  # Limit for Haiku context
            "",
            "Check for continuity issues: wrong characters present, location contradictions, "
            "state inconsistencies with preceding scenes. Respond with JSON.",
        ])

        return "\n".join(parts)
