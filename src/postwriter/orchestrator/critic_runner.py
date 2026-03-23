"""Critic runner: parallel execution of all validators and critics."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field

from postwriter.llm.client import LLMClient
from postwriter.scoring.vectors import ScoreVectorData, scores_from_validation
from postwriter.types import ValidationResult
from postwriter.validation.base import ValidationContext, ValidationSuite

logger = logging.getLogger(__name__)


@dataclass
class EvaluationResult:
    """Complete evaluation of a draft: hard results, soft results, and scores."""

    hard_results: list[ValidationResult] = field(default_factory=list)
    soft_results: list[ValidationResult] = field(default_factory=list)
    scores: ScoreVectorData = field(default_factory=ScoreVectorData)
    hard_pass: bool = True

    @property
    def all_results(self) -> list[ValidationResult]:
        return self.hard_results + self.soft_results

    def failed_hard(self) -> list[ValidationResult]:
        return [r for r in self.hard_results if r.passed is False]

    def weak_dimensions(self, threshold: float = 0.4) -> list[ValidationResult]:
        return [r for r in self.soft_results if r.score is not None and r.score < threshold]


class CriticRunner:
    """Runs all hard validators and soft critics in parallel against a draft."""

    def __init__(self, llm: LLMClient | None = None) -> None:
        self._suite = ValidationSuite(llm)

    async def evaluate(self, ctx: ValidationContext) -> EvaluationResult:
        """Run all validators and critics, return unified evaluation."""
        # Run hard and soft in parallel
        hard_results, soft_results = await asyncio.gather(
            self._suite.run_hard(ctx),
            self._suite.run_soft(ctx),
        )

        # Build score vector from all results
        all_results = hard_results + soft_results
        scores = scores_from_validation(all_results)

        return EvaluationResult(
            hard_results=hard_results,
            soft_results=soft_results,
            scores=scores,
            hard_pass=scores.hard_pass,
        )

    async def evaluate_hard_only(self, ctx: ValidationContext) -> EvaluationResult:
        """Run only hard validators (faster, for repair loop iterations)."""
        hard_results = await self._suite.run_hard(ctx)
        scores = scores_from_validation(hard_results)

        return EvaluationResult(
            hard_results=hard_results,
            soft_results=[],
            scores=scores,
            hard_pass=scores.hard_pass,
        )
