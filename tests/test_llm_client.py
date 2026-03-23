"""Tests for the LLM client and token budget."""

import pytest

from postwriter.errors import BudgetExhausted
from postwriter.llm.budget import TokenBudget
from postwriter.types import ModelTier


def test_budget_record_and_query():
    budget = TokenBudget()
    budget.record(ModelTier.SONNET, input_tokens=1000, output_tokens=500)
    budget.record(ModelTier.SONNET, input_tokens=2000, output_tokens=1000)

    usage = budget.usage[ModelTier.SONNET]
    assert usage.input_tokens == 3000
    assert usage.output_tokens == 1500
    assert usage.total_tokens == 4500
    assert usage.calls == 2


def test_budget_unlimited_by_default():
    budget = TokenBudget()
    budget.record(ModelTier.OPUS, 1_000_000, 500_000)
    # Should not raise
    budget.check(ModelTier.OPUS)
    assert budget.remaining(ModelTier.OPUS) is None


def test_budget_limit_enforcement():
    budget = TokenBudget(limits={ModelTier.HAIKU: 10_000})
    budget.record(ModelTier.HAIKU, 8_000, 3_000)

    with pytest.raises(BudgetExhausted) as exc_info:
        budget.check(ModelTier.HAIKU)
    assert exc_info.value.tier == "haiku"
    assert exc_info.value.used == 11_000


def test_budget_remaining():
    budget = TokenBudget(limits={ModelTier.SONNET: 100_000})
    budget.record(ModelTier.SONNET, 30_000, 10_000)

    assert budget.remaining(ModelTier.SONNET) == 60_000


def test_budget_summary():
    budget = TokenBudget(limits={ModelTier.OPUS: 50_000})
    budget.record(ModelTier.OPUS, 10_000, 5_000)
    budget.record(ModelTier.SONNET, 20_000, 10_000)

    summary = budget.summary()
    assert summary["opus"]["total_tokens"] == 15_000
    assert summary["opus"]["remaining"] == 35_000
    assert summary["sonnet"]["total_tokens"] == 30_000
    assert summary["sonnet"]["remaining"] is None
    assert summary["haiku"]["calls"] == 0
