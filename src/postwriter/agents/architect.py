"""Architect agents: premise design and structural spine."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from postwriter.agents.base import BaseAgent
from postwriter.types import AgentContext, ModelTier


# ---------------------------------------------------------------------------
# Response models
# ---------------------------------------------------------------------------


class PremiseResponse(BaseModel):
    premise: str = Field(description="2-3 paragraph summary of the novel's core situation and trajectory")
    controlling_design: dict[str, Any] = Field(
        description="Architectural spine: central_question, arc_shape, turning_points, emotional_trajectory, plot_internal_relationship, tonal_range"
    )
    thematic_architecture: dict[str, Any] = Field(
        description="How themes are embodied: character_tensions, symbolic_patterns, structural_embodiments"
    )


class SpineResponse(BaseModel):
    acts: list[dict[str, Any]] = Field(
        description="List of acts, each with: name, ordinal, purpose, emotional_arc, chapter_count"
    )
    major_turning_points: list[dict[str, Any]] = Field(
        description="Key structural turning points with: description, approximate_position, function"
    )
    arc_summary: str = Field(description="One-paragraph summary of the full arc shape")


# ---------------------------------------------------------------------------
# Agents
# ---------------------------------------------------------------------------


class PremiseArchitect(BaseAgent):
    """Generates a novel premise and controlling design from a creative brief."""

    role = "premise_architect"
    model_tier = ModelTier.OPUS
    template_name = "architect_premise.j2"
    response_model = PremiseResponse

    def build_template_context(self, context: AgentContext) -> dict[str, Any]:
        brief = context.extra.get("creative_brief", {})
        return {
            "genre": brief.get("genre", ""),
            "setting": brief.get("setting", ""),
            "time_period": brief.get("time_period", ""),
            "tone": brief.get("tone", ""),
            "protagonist": brief.get("protagonist", ""),
            "central_conflict": brief.get("central_conflict", ""),
            "ending_direction": brief.get("ending_direction", ""),
            "themes": brief.get("themes", []),
            "constraints": brief.get("constraints", []),
            "user_context": context.user_context,
        }

    def build_system_prompt(self, context: AgentContext) -> str:
        base = (
            "You are a master fiction architect with deep knowledge of narrative structure, "
            "literary tradition, and genre conventions. Your task is to design a novel premise "
            "and controlling design that will sustain a full-length manuscript.\n\n"
            "Design for emotional credibility, thematic depth, and structural integrity. "
            "Themes should be embodied through character and situation, never stated directly."
        )
        # Append user context if available
        if context.user_context:
            base += "\n\n## User-Provided Reference Materials\n\n"
            for ctx in context.user_context:
                base += f"### {ctx.get('name', 'Reference')} ({ctx.get('type', 'unknown')})\n"
                base += ctx.get("content", "") + "\n\n"
        return base

    def _max_tokens(self) -> int:
        return 8192

    def _temperature(self) -> float:
        return 1.0


class SpineArchitect(BaseAgent):
    """Designs the structural spine (acts and major movements) from a premise."""

    role = "spine_architect"
    model_tier = ModelTier.OPUS
    template_name = "architect_spine.j2"
    response_model = SpineResponse

    def build_template_context(self, context: AgentContext) -> dict[str, Any]:
        return {
            "premise": context.premise,
            "controlling_design": context.controlling_design,
            "target_word_count": context.extra.get("target_word_count", 80000),
            "target_chapters": context.extra.get("target_chapters", "30-40"),
            "user_context": context.user_context,
        }

    def build_system_prompt(self, context: AgentContext) -> str:
        return (
            "You are a master fiction architect. Given a premise and controlling design, "
            "design the structural spine of the novel: its acts, major movements, and "
            "turning points.\n\n"
            "Each act should have a clear purpose and emotional trajectory. "
            "Distribute tension, revelation, and release across the full arc. "
            "The spine should support the controlling design without over-determining "
            "individual scenes."
        )

    def _max_tokens(self) -> int:
        return 8192
