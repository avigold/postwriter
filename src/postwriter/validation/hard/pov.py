"""POV validator: checks that only the POV character's internals are narrated."""

from __future__ import annotations

import json

from pydantic import BaseModel, Field

from postwriter.llm.client import LLMClient
from postwriter.types import ModelTier, ValidationResult
from postwriter.validation.base import BaseValidator, ValidationContext, register_hard_validator


class POVCheck(BaseModel):
    passed: bool
    violations: list[dict[str, str]] = Field(default_factory=list)
    reasoning: str = ""


@register_hard_validator("pov")
class POVValidator(BaseValidator):
    """Checks that the prose respects POV constraints.

    In limited third person, the narrator should only access the internals
    (thoughts, feelings, sensations) of the POV character.
    """

    async def validate(self, ctx: ValidationContext) -> ValidationResult:
        if not self._llm:
            return ValidationResult(
                validator_name=self.name, is_hard=True, passed=True, score=None,
                diagnosis="No LLM available, skipping POV check.",
            )

        pov_char = ctx.scene_brief.get("pov_character_id") or ctx.scene_brief.get("pov_character", "unknown")
        characters = [c.get("name", "") for c in ctx.characters]

        prompt = (
            f"## POV Character: {pov_char}\n"
            f"## All Characters in Scene: {', '.join(characters)}\n\n"
            f"## Prose:\n{ctx.prose[:3000]}\n\n"
            "Check if this prose violates limited third-person POV. The narrator should ONLY "
            f"access the internal thoughts, feelings, and sensations of {pov_char}. "
            "Other characters' internals should only be inferred from external observation.\n\n"
            "Respond with JSON: {passed: bool, violations: [{character, description, quote}], reasoning: str}"
        )

        response = await self._llm.complete(
            tier=ModelTier.HAIKU,
            messages=[{"role": "user", "content": prompt}],
            system="You are a POV consistency checker. Be strict about POV violations.",
            max_tokens=1024,
            temperature=0.0,
        )

        try:
            text = response.text.strip()
            if text.startswith("```"):
                text = "\n".join(text.split("\n")[1:-1])
            check = POVCheck.model_validate(json.loads(text))
        except Exception:
            return ValidationResult(
                validator_name=self.name, is_hard=True, passed=True, score=None,
                diagnosis="Could not parse POV check response.",
            )

        return ValidationResult(
            validator_name=self.name,
            is_hard=True,
            passed=check.passed,
            score=None,
            diagnosis=check.reasoning,
            evidence=check.violations,
        )
