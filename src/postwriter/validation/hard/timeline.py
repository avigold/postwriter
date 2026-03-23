"""Timeline validator: checks temporal consistency."""

from __future__ import annotations

import json

from pydantic import BaseModel, Field

from postwriter.types import ModelTier, ValidationResult
from postwriter.validation.base import BaseValidator, ValidationContext, register_hard_validator


class TimelineCheck(BaseModel):
    passed: bool
    issues: list[dict[str, str]] = Field(default_factory=list)
    reasoning: str = ""


@register_hard_validator("timeline")
class TimelineValidator(BaseValidator):
    """Checks temporal consistency of the scene prose."""

    async def validate(self, ctx: ValidationContext) -> ValidationResult:
        if not self._llm:
            return ValidationResult(
                validator_name=self.name, is_hard=True, passed=True, score=None,
                diagnosis="No LLM available, skipping timeline check.",
            )

        prompt = (
            f"## Scene Time Marker: {ctx.scene_brief.get('time_marker', 'unspecified')}\n\n"
        )

        if ctx.preceding_scenes:
            prompt += "## Preceding Scenes:\n"
            for ps in ctx.preceding_scenes[-2:]:
                prompt += f"- Time: {ps.get('time_marker', '?')}, Location: {ps.get('location', '?')}\n"
            prompt += "\n"

        prompt += (
            f"## Current Scene Prose:\n{ctx.prose[:2000]}\n\n"
            "Check for timeline issues:\n"
            "- Does the prose contradict the stated time marker?\n"
            "- Are there impossible temporal jumps from the preceding scene?\n"
            "- Do events happen in a plausible temporal order within the scene?\n\n"
            "Respond with JSON: {passed: bool, issues: [{type, description}], reasoning: str}"
        )

        response = await self._llm.complete(
            tier=ModelTier.HAIKU,
            messages=[{"role": "user", "content": prompt}],
            system="You are a timeline consistency checker for fiction. Be precise.",
            max_tokens=1024,
            temperature=0.0,
        )

        try:
            text = response.text.strip()
            if text.startswith("```"):
                text = "\n".join(text.split("\n")[1:-1])
            check = TimelineCheck.model_validate(json.loads(text))
        except Exception:
            return ValidationResult(
                validator_name=self.name, is_hard=True, passed=True, score=None,
                diagnosis="Could not parse timeline check response.",
            )

        return ValidationResult(
            validator_name=self.name,
            is_hard=True,
            passed=check.passed,
            score=None,
            diagnosis=check.reasoning,
            evidence=check.issues,
        )
