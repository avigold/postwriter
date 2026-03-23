"""Validation framework: base classes, context, and suite runner."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from postwriter.llm.client import LLMClient
from postwriter.types import ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class ValidationContext:
    """All information a validator needs to check a scene draft."""

    prose: str
    scene_brief: dict[str, Any]
    chapter_brief: dict[str, Any] = field(default_factory=dict)
    characters: list[dict[str, Any]] = field(default_factory=list)
    character_states: list[dict[str, Any]] = field(default_factory=list)
    preceding_scenes: list[dict[str, Any]] = field(default_factory=list)
    open_promises: list[dict[str, Any]] = field(default_factory=list)
    style_profile: dict[str, Any] = field(default_factory=dict)
    manuscript_id: str = ""


class BaseValidator:
    """Base class for all validators (hard and soft)."""

    name: str = "base"
    is_hard: bool = True

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm

    async def validate(self, ctx: ValidationContext) -> ValidationResult:
        raise NotImplementedError


# Registry for auto-discovery
_HARD_VALIDATORS: dict[str, type[BaseValidator]] = {}
_SOFT_CRITICS: dict[str, type[BaseValidator]] = {}


def register_hard_validator(name: str):
    """Decorator to register a hard validator."""
    def decorator(cls: type[BaseValidator]):
        cls.name = name
        cls.is_hard = True
        _HARD_VALIDATORS[name] = cls
        return cls
    return decorator


def register_soft_critic(name: str):
    """Decorator to register a soft critic."""
    def decorator(cls: type[BaseValidator]):
        cls.name = name
        cls.is_hard = False
        _SOFT_CRITICS[name] = cls
        return cls
    return decorator


class ValidationSuite:
    """Runs all registered validators/critics in parallel against a draft."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._llm = llm

    def get_hard_validators(self) -> list[BaseValidator]:
        return [cls(self._llm) for cls in _HARD_VALIDATORS.values()]

    def get_soft_critics(self) -> list[BaseValidator]:
        return [cls(self._llm) for cls in _SOFT_CRITICS.values()]

    async def run_hard(self, ctx: ValidationContext) -> list[ValidationResult]:
        """Run all hard validators in parallel."""
        validators = self.get_hard_validators()
        if not validators:
            return []

        tasks = [v.validate(ctx) for v in validators]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = []
        for v, r in zip(validators, results):
            if isinstance(r, Exception):
                logger.error("Validator %s failed: %s", v.name, r)
                valid_results.append(ValidationResult(
                    validator_name=v.name,
                    is_hard=True,
                    passed=False,
                    score=None,
                    diagnosis=f"Validator error: {r}",
                ))
            else:
                valid_results.append(r)
        return valid_results

    async def run_soft(self, ctx: ValidationContext) -> list[ValidationResult]:
        """Run all soft critics in parallel."""
        critics = self.get_soft_critics()
        if not critics:
            return []

        tasks = [c.validate(ctx) for c in critics]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        valid_results = []
        for c, r in zip(critics, results):
            if isinstance(r, Exception):
                logger.error("Critic %s failed: %s", c.name, r)
                valid_results.append(ValidationResult(
                    validator_name=c.name,
                    is_hard=False,
                    passed=None,
                    score=0.5,
                    diagnosis=f"Critic error: {r}",
                ))
            else:
                valid_results.append(r)
        return valid_results

    async def run_all(self, ctx: ValidationContext) -> list[ValidationResult]:
        """Run all hard validators and soft critics."""
        hard, soft = await asyncio.gather(
            self.run_hard(ctx),
            self.run_soft(ctx),
        )
        return hard + soft
