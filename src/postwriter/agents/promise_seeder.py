"""Promise seeder: identifies initial narrative promises from the spine and plan."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from postwriter.agents.base import BaseAgent
from postwriter.types import AgentContext, ModelTier


class PromiseSeed(BaseModel):
    type: str = Field(description="One of: plot, emotional, thematic, symbolic, tonal, rhetorical")
    description: str = Field(description="What the promise is")
    salience: float = Field(ge=0, le=1, description="How important this promise is to the reader")
    expected_introduction: str = Field(
        description="When/where this promise is likely introduced (e.g., 'act 1, chapter 2')"
    )
    expected_resolution_window: str = Field(
        description="When this promise should be resolved (e.g., 'act 3' or 'climax')"
    )


class PromiseSeedResponse(BaseModel):
    promises: list[PromiseSeed]
    notes: str = Field(
        default="",
        description="Notes on how these promises interlock and create reader tension",
    )


class PromiseSeeder(BaseAgent):
    """Identifies initial narrative promises and obligations from the novel's design."""

    role = "promise_seeder"
    model_tier = ModelTier.SONNET
    template_name = "promise_seeder.j2"
    response_model = PromiseSeedResponse

    def build_template_context(self, context: AgentContext) -> dict[str, Any]:
        return {
            "premise": context.premise,
            "controlling_design": context.controlling_design,
            "characters": context.characters,
            "acts": context.extra.get("acts", []),
        }

    def build_system_prompt(self, context: AgentContext) -> str:
        return (
            "You are a narrative promise analyst. A promise is anything in a story "
            "that creates a burden on the future — an expectation the reader holds "
            "that must eventually be addressed.\n\n"
            "Identify all significant promises that the novel's premise, characters, "
            "and structure create. Include plot promises (Chekhov's guns), emotional "
            "promises (relationships that must resolve), thematic promises (questions "
            "the novel implicitly asks), symbolic promises (loaded objects or images), "
            "and tonal promises (moods that demand payoff).\n\n"
            "Be thorough but not exhaustive. Focus on promises that carry real reader weight."
        )

    def _max_tokens(self) -> int:
        return 4096
