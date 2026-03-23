"""Knowledge state validator: checks that characters don't act on unknown information."""

from __future__ import annotations

import json

from pydantic import BaseModel, Field

from postwriter.types import ModelTier, ValidationResult
from postwriter.validation.base import BaseValidator, ValidationContext, register_hard_validator


class KnowledgeCheck(BaseModel):
    passed: bool
    violations: list[dict[str, str]] = Field(default_factory=list)
    reasoning: str = ""


@register_hard_validator("knowledge_state")
class KnowledgeStateValidator(BaseValidator):
    """Checks that characters don't act on information they shouldn't have."""

    async def validate(self, ctx: ValidationContext) -> ValidationResult:
        if not self._llm:
            return ValidationResult(
                validator_name=self.name, is_hard=True, passed=True, score=None,
                diagnosis="No LLM available, skipping knowledge state check.",
            )

        # Only meaningful if we have character state data
        if not ctx.character_states:
            return ValidationResult(
                validator_name=self.name, is_hard=True, passed=True, score=None,
                diagnosis="No character states to check against.",
            )

        prompt = "## Character Knowledge States\n\n"
        for cs in ctx.character_states:
            char_id = cs.get("character_id", "unknown")
            # Try to find character name
            char_name = char_id
            for c in ctx.characters:
                if c.get("id") == char_id:
                    char_name = c.get("name", char_id)
                    break
            prompt += f"### {char_name}\n"
            prompt += f"Knows: {json.dumps(cs.get('knowledge_state', {}))}\n"
            prompt += f"Does NOT know: (anything not listed above)\n\n"

        prompt += (
            f"## Scene Prose:\n{ctx.prose[:3000]}\n\n"
            "Check if any character acts on, references, or reveals knowledge they "
            "should not have according to their knowledge state. Characters can make "
            "reasonable inferences, but should not know specific facts they haven't learned.\n\n"
            "Respond with JSON: {passed: bool, violations: [{character, knowledge_used, description}], reasoning: str}"
        )

        response = await self._llm.complete(
            tier=ModelTier.HAIKU,
            messages=[{"role": "user", "content": prompt}],
            system="You are a knowledge-state checker for fiction. Flag cases where characters know things they shouldn't.",
            max_tokens=1024,
            temperature=0.0,
        )

        try:
            text = response.text.strip()
            if text.startswith("```"):
                text = "\n".join(text.split("\n")[1:-1])
            check = KnowledgeCheck.model_validate(json.loads(text))
        except Exception:
            return ValidationResult(
                validator_name=self.name, is_hard=True, passed=True, score=None,
                diagnosis="Could not parse knowledge state check response.",
            )

        return ValidationResult(
            validator_name=self.name,
            is_hard=True,
            passed=check.passed,
            score=None,
            diagnosis=check.reasoning,
            evidence=check.violations,
        )
