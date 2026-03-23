"""Tests for configuration profiles."""

from postwriter.config import LLMSettings, OrchestratorSettings
from postwriter.profiles import PROFILES, apply_profile, list_profiles

import pytest


def test_profiles_exist():
    assert "fast_draft" in PROFILES
    assert "high_quality" in PROFILES
    assert "budget_conscious" in PROFILES


def test_apply_fast_draft():
    settings = OrchestratorSettings()
    apply_profile("fast_draft", settings)

    assert settings.max_repair_rounds == 1
    assert settings.default_branch_count == 2


def test_apply_high_quality():
    settings = OrchestratorSettings()
    apply_profile("high_quality", settings)

    assert settings.max_repair_rounds == 5
    assert settings.pivotal_branch_count == 5
    assert settings.min_improvement_delta == 0.01


def test_apply_budget_conscious():
    settings = OrchestratorSettings()
    apply_profile("budget_conscious", settings)

    assert settings.default_branch_count == 2
    assert settings.pivotal_branch_count == 2


def test_apply_unknown_profile():
    settings = OrchestratorSettings()
    with pytest.raises(ValueError, match="Unknown profile"):
        apply_profile("nonexistent", settings)


def test_list_profiles():
    profiles = list_profiles()
    assert len(profiles) == 3
    names = {p["name"] for p in profiles}
    assert names == {"fast_draft", "high_quality", "budget_conscious"}
