"""Scene planner agent: creates precise scene briefs from chapter plans."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from postwriter.agents.base import BaseAgent
from postwriter.types import AgentContext, ModelTier


class SceneBrief(BaseModel):
    ordinal: int
    pov_character: str
    location: str
    time_marker: str = Field(description="When this scene takes place relative to the story timeline")
    purpose: str = Field(description="The dramatic purpose of this scene")
    conflict: str = Field(description="The central conflict or tension in this scene")
    stakes: str = Field(description="What is at risk in this scene")
    revelation: str | None = Field(
        default=None,
        description="What is revealed, if anything",
    )
    emotional_turn: str = Field(
        description="How the emotional state shifts from scene start to end"
    )
    dramatic_function: str = Field(
        description="The scene's role in the larger structure (e.g., escalation, relief, pivot)"
    )
    characters_present: list[str] = Field(description="Names of characters in this scene")
    prohibited_moves: list[str] = Field(
        default_factory=list,
        description="Things this scene must NOT do",
    )
    themes_touched: list[str] = Field(default_factory=list)
    symbols_touched: list[str] = Field(default_factory=list)
    setup_links: list[str] = Field(
        default_factory=list,
        description="What earlier setups this scene pays off",
    )
    payoff_links: list[str] = Field(
        default_factory=list,
        description="What this scene sets up for later",
    )
    state_mutations: dict[str, Any] = Field(
        default_factory=dict,
        description="What changes in the story state after this scene",
    )
    is_pivotal: bool = Field(
        default=False,
        description="Whether this is a structurally critical scene deserving extra branches",
    )


class ScenePlanResponse(BaseModel):
    scenes: list[SceneBrief]


class ScenePlanner(BaseAgent):
    """Creates detailed scene briefs for a chapter."""

    role = "scene_planner"
    model_tier = ModelTier.SONNET
    template_name = "scene_planner.j2"
    response_model = ScenePlanResponse

    def build_template_context(self, context: AgentContext) -> dict[str, Any]:
        return {
            "premise": context.premise,
            "chapter_brief": context.chapter_brief,
            "characters": context.characters,
            "character_states": context.character_states,
            "open_promises": context.open_promises,
            "preceding_scenes": context.preceding_scenes,
            "style_profile": context.style_profile,
            "user_context": context.user_context,
        }

    def build_system_prompt(self, context: AgentContext) -> str:
        return (
            "You are a scene-level narrative planner. Given a chapter brief and the "
            "current story state, design precise scene briefs that will guide scene writers.\n\n"
            "Each scene must have a clear conflict, stakes, and emotional turn. "
            "Specify what the scene must NOT do (prohibited moves). "
            "Mark structurally pivotal scenes that deserve extra drafting attention. "
            "Track what changes in the story state after each scene."
        )

    def _max_tokens(self) -> int:
        return 8192
