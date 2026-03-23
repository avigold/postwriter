"""Character designer agent: builds a full cast from the premise and spine."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from postwriter.agents.base import BaseAgent
from postwriter.types import AgentContext, ModelTier


class CharacterDesign(BaseModel):
    name: str
    aliases: list[str] = Field(default_factory=list)
    age: str | None = None
    biography: str = Field(description="2-4 sentence biography")
    motives: dict[str, str] = Field(description="Primary and secondary motives")
    fears: list[str] = Field(default_factory=list)
    desires: list[str] = Field(default_factory=list)
    secrets: list[str] = Field(default_factory=list)
    social_position: str = ""
    speaking_traits: dict[str, str] = Field(
        description="Verbal patterns, vocabulary level, rhythms, tics"
    )
    movement_traits: dict[str, str] = Field(
        default_factory=dict,
        description="Physical mannerisms, gestures, posture",
    )
    recurring_gestures: list[str] = Field(default_factory=list)
    moral_constraints: list[str] = Field(default_factory=list)
    arc_hypothesis: str = Field(description="Where this character starts and where they might end")
    is_pov_character: bool = False
    relationships: list[dict[str, str]] = Field(
        default_factory=list,
        description="Relationships to other characters: [{character, type, description}]",
    )


class CastResponse(BaseModel):
    characters: list[CharacterDesign] = Field(
        description="Full cast of main and significant secondary characters"
    )
    relationship_dynamics: str = Field(
        description="Paragraph describing how the cast creates tension and complements the themes"
    )


class CharacterDesigner(BaseAgent):
    """Designs the full cast of characters from the premise and spine."""

    role = "character_designer"
    model_tier = ModelTier.OPUS
    template_name = "character_designer.j2"
    response_model = CastResponse

    def build_template_context(self, context: AgentContext) -> dict[str, Any]:
        return {
            "premise": context.premise,
            "controlling_design": context.controlling_design,
            "themes": context.extra.get("themes", []),
            "user_context": context.user_context,
            "existing_characters": context.characters,
        }

    def build_system_prompt(self, context: AgentContext) -> str:
        base = (
            "You are a master character designer for literary fiction. "
            "Create characters who are psychologically complex, internally contradictory, "
            "and dramatically productive. Each character should serve the story's thematic "
            "architecture while feeling like an autonomous person, not a symbolic function.\n\n"
            "Design speaking traits that are distinct but not caricatured. "
            "Give each character at least one secret and one moral constraint. "
            "Relationships should create productive tension."
        )
        if context.user_context:
            char_context = [c for c in context.user_context if c.get("type") == "characters"]
            if char_context:
                base += "\n\n## User-Provided Character Notes\n\n"
                for ctx in char_context:
                    base += ctx.get("content", "") + "\n\n"
        return base

    def _max_tokens(self) -> int:
        return 8192
