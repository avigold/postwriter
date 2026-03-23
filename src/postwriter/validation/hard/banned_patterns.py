"""Banned patterns validator: pure rule-based check for forbidden phrases and moves."""

from __future__ import annotations

import re

from postwriter.types import ValidationResult
from postwriter.validation.base import BaseValidator, ValidationContext, register_hard_validator


@register_hard_validator("banned_patterns")
class BannedPatternsValidator(BaseValidator):
    """Checks for banned phrases and patterns in the prose. Pure rule-based, no LLM."""

    async def validate(self, ctx: ValidationContext) -> ValidationResult:
        violations: list[dict[str, str]] = []
        prose_lower = ctx.prose.lower()

        # Check banned phrases from style profile
        banned_phrases = ctx.style_profile.get("banned_phrases", [])
        for phrase in banned_phrases:
            if phrase.lower() in prose_lower:
                # Find approximate position
                idx = prose_lower.index(phrase.lower())
                context_start = max(0, idx - 30)
                context_end = min(len(ctx.prose), idx + len(phrase) + 30)
                violations.append({
                    "type": "banned_phrase",
                    "phrase": phrase,
                    "context": ctx.prose[context_start:context_end],
                })

        # Check for common AI writing tics that should always be caught
        ai_tics = [
            r"\ba sense of\b",
            r"\bcouldn't help but\b",
            r"\ba (wave|surge|jolt) of\b",
            r"\bthe weight of\b.*\b(settled|pressed|hung)\b",
            r"\bin that moment\b",
            r"\blittle did (he|she|they) know\b",
            r"\btime seemed to (slow|stop|freeze)\b",
            r"\beverything changed\b",
        ]
        for pattern in ai_tics:
            matches = list(re.finditer(pattern, ctx.prose, re.IGNORECASE))
            for m in matches:
                violations.append({
                    "type": "ai_tic",
                    "phrase": m.group(),
                    "context": ctx.prose[max(0, m.start() - 20):m.end() + 20],
                })

        if violations:
            diagnosis = f"Found {len(violations)} banned pattern(s):\n"
            for v in violations[:5]:  # Limit diagnosis length
                diagnosis += f"  - [{v['type']}] \"{v['phrase']}\" in: ...{v['context']}...\n"
            return ValidationResult(
                validator_name=self.name,
                is_hard=True,
                passed=False,
                score=None,
                diagnosis=diagnosis.strip(),
                evidence=violations,
            )

        return ValidationResult(
            validator_name=self.name,
            is_hard=True,
            passed=True,
            score=None,
            diagnosis="No banned patterns found.",
        )
