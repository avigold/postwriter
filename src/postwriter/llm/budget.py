"""Token budget tracking per model tier."""

from __future__ import annotations

from dataclasses import dataclass, field

from postwriter.errors import BudgetExhausted
from postwriter.types import ModelTier


@dataclass
class TierUsage:
    input_tokens: int = 0
    output_tokens: int = 0
    calls: int = 0

    @property
    def total_tokens(self) -> int:
        return self.input_tokens + self.output_tokens


@dataclass
class TokenBudget:
    """Tracks token usage across model tiers with optional hard limits."""

    limits: dict[ModelTier, int] = field(default_factory=dict)
    usage: dict[ModelTier, TierUsage] = field(default_factory=lambda: {
        ModelTier.OPUS: TierUsage(),
        ModelTier.SONNET: TierUsage(),
        ModelTier.HAIKU: TierUsage(),
    })

    def record(self, tier: ModelTier, input_tokens: int, output_tokens: int) -> None:
        self.usage[tier].input_tokens += input_tokens
        self.usage[tier].output_tokens += output_tokens
        self.usage[tier].calls += 1

    def check(self, tier: ModelTier) -> None:
        """Raise BudgetExhausted if the tier's budget is exceeded."""
        limit = self.limits.get(tier, 0)
        if limit > 0 and self.usage[tier].total_tokens >= limit:
            raise BudgetExhausted(tier.value, self.usage[tier].total_tokens, limit)

    def remaining(self, tier: ModelTier) -> int | None:
        """Return remaining tokens for a tier, or None if unlimited."""
        limit = self.limits.get(tier, 0)
        if limit <= 0:
            return None
        return max(0, limit - self.usage[tier].total_tokens)

    def summary(self) -> dict[str, dict[str, int | None]]:
        return {
            tier.value: {
                "input_tokens": self.usage[tier].input_tokens,
                "output_tokens": self.usage[tier].output_tokens,
                "total_tokens": self.usage[tier].total_tokens,
                "calls": self.usage[tier].calls,
                "remaining": self.remaining(tier),
            }
            for tier in ModelTier
        }
