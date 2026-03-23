"""Local rewriter agent: applies targeted repairs to scene prose."""

from __future__ import annotations

from typing import Any

from postwriter.agents.base import BaseAgent
from postwriter.repair.actions import RepairActionSpec
from postwriter.types import AgentContext, ModelTier


class LocalRewriter(BaseAgent):
    """Rewrites targeted aspects of scene prose based on repair instructions.

    Returns revised prose (raw text, not structured output).
    """

    role = "local_rewriter"
    model_tier = ModelTier.SONNET
    template_name = "local_rewriter.j2"
    response_model = None  # Returns prose

    def __init__(self, *args: Any, repair_actions: list[RepairActionSpec] | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._repairs = repair_actions or []

    def build_system_prompt(self, context: AgentContext) -> str:
        parts = [
            "You are a precise fiction rewriter. Your job is to repair specific issues "
            "in scene prose while preserving everything that works.",
            "",
            "CRITICAL RULES:",
            "- Output ONLY the revised complete scene prose. No commentary.",
            "- Make the MINIMUM changes needed to fix the issues.",
            "- Preserve the scene's emotional arc, voice, and purpose.",
            "- Do not gratuitously paraphrase unchanged sections.",
            "- Respect all preserve constraints listed below.",
        ]
        return "\n".join(parts)

    def build_template_context(self, context: AgentContext) -> dict[str, Any]:
        return {
            "scene_brief": context.scene_brief,
            "style_profile": context.style_profile,
            "current_prose": context.extra.get("current_prose", ""),
            "repair_actions": [
                {
                    "priority": r.priority.name,
                    "dimension": r.target_dimension,
                    "instruction": r.instruction,
                    "preserve": r.preserve_constraints,
                    "banned": r.banned_interventions,
                }
                for r in self._repairs
            ],
        }

    def _max_tokens(self) -> int:
        return 8192

    def _temperature(self) -> float:
        return 0.7  # Slightly lower than drafting for more controlled edits
