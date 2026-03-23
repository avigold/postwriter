"""Chapter planner agent: converts act structure into detailed chapter briefs."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from postwriter.agents.base import BaseAgent
from postwriter.types import AgentContext, ModelTier


class ChapterBrief(BaseModel):
    ordinal: int
    title: str = Field(description="Working title for the chapter")
    function: str = Field(description="What this chapter accomplishes dramatically")
    emotional_contour: dict[str, Any] = Field(
        description="{opening_emotion, peak_emotion, closing_emotion, arc_shape}"
    )
    opening_pressure: float = Field(ge=0, le=1, description="Tension level at chapter opening")
    closing_pressure: float = Field(ge=0, le=1, description="Tension level at chapter close")
    scene_count: int = Field(ge=1, le=8, description="Number of scenes in this chapter")
    scene_summaries: list[str] = Field(
        description="One-sentence summary of each scene's purpose"
    )
    themes_active: list[str] = Field(description="Themes engaged in this chapter")
    motif_targets: list[str] = Field(default_factory=list)
    pov_character: str = Field(description="Name of the POV character for this chapter")
    transition_from_previous: str = Field(
        default="",
        description="How this chapter connects to the previous one",
    )
    contrast_with_neighbors: str = Field(
        default="",
        description="How this chapter differs in tone/pace from adjacent chapters",
    )


class ChapterPlanResponse(BaseModel):
    chapters: list[ChapterBrief]
    rhythm_notes: str = Field(
        description="Notes on the pacing and rhythm across this sequence of chapters"
    )


class ChapterPlanner(BaseAgent):
    """Plans detailed chapter briefs for an act or the full manuscript."""

    role = "chapter_planner"
    model_tier = ModelTier.SONNET
    template_name = "chapter_planner.j2"
    response_model = ChapterPlanResponse

    def build_template_context(self, context: AgentContext) -> dict[str, Any]:
        return {
            "premise": context.premise,
            "controlling_design": context.controlling_design,
            "act": context.extra.get("act", {}),
            "characters": context.characters,
            "themes": context.extra.get("themes", []),
            "preceding_chapters": context.extra.get("preceding_chapters", []),
            "style_profile": context.style_profile,
            "user_context": context.user_context,
        }

    def build_system_prompt(self, context: AgentContext) -> str:
        return (
            "You are a chapter-level narrative planner. Given the act structure and "
            "overall controlling design, break the act into individual chapters with "
            "precise dramatic functions.\n\n"
            "Each chapter should have a clear emotional contour — not every chapter "
            "should escalate. Vary pressure, pace, and mode. Distribute revelations "
            "and concealments deliberately. Ensure chapter transitions create forward "
            "momentum without telegraphing."
        )

    def _max_tokens(self) -> int:
        return 8192
