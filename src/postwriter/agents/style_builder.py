"""Style profile builder: converts voice preferences into a complete StyleProfile."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from postwriter.agents.base import BaseAgent
from postwriter.types import AgentContext, ModelTier


class StyleProfileResponse(BaseModel):
    voice_description: str = Field(description="Paragraph describing the target narrative voice")
    directness: float = Field(ge=0, le=1, description="0=oblique, 1=direct")
    subtext_target: float = Field(ge=0, le=1, description="How much meaning should live beneath the surface")
    irony_target: float = Field(ge=0, le=1, description="Degree of ironic distance in the narration")
    lyricism_target: float = Field(ge=0, le=1, description="0=spare/plain, 1=highly lyrical")
    sentence_length_bands: dict[str, Any] = Field(
        description="Target distribution: {short_pct, medium_pct, long_pct, avg_words}"
    )
    dialogue_density_band: dict[str, Any] = Field(
        description="{min_pct, max_pct, target_pct} of scene text that is dialogue"
    )
    metaphor_density_band: dict[str, Any] = Field(
        description="{min_per_1000, max_per_1000} target metaphor density"
    )
    fragment_tolerance: float = Field(ge=0, le=1, description="Tolerance for sentence fragments")
    exposition_tolerance: float = Field(ge=0, le=1)
    abstraction_tolerance: float = Field(ge=0, le=1)
    preferred_imagery_domains: list[str] = Field(
        description="Source domains for metaphor/simile (e.g., 'architecture', 'water', 'glass')"
    )
    banned_imagery_domains: list[str] = Field(default_factory=list)
    banned_phrases: list[str] = Field(
        description="Phrases to never use (cliches, tics, etc.)"
    )
    banned_moves: list[str] = Field(
        default_factory=list,
        description="Narrative moves to avoid (e.g., 'dream sequence reveal', 'mirror description')",
    )
    disfavoured_devices: list[str] = Field(default_factory=list)
    recurrence_caps: dict[str, int] = Field(
        default_factory=dict,
        description="Max occurrences per chapter for specific devices",
    )


class StyleBuilder(BaseAgent):
    """Builds a complete style profile from the creative brief and voice preferences."""

    role = "style_builder"
    model_tier = ModelTier.SONNET
    template_name = "style_builder.j2"
    response_model = StyleProfileResponse

    def build_template_context(self, context: AgentContext) -> dict[str, Any]:
        brief = context.extra.get("creative_brief", {})
        return {
            "premise": context.premise,
            "genre": brief.get("genre", ""),
            "tone": brief.get("tone", ""),
            "voice_preferences": brief.get("voice_preferences", ""),
            "user_context": context.user_context,
        }

    def build_system_prompt(self, context: AgentContext) -> str:
        base = (
            "You are an expert on prose style and narrative voice. "
            "Given a novel premise and the author's voice preferences, "
            "design a complete stylistic profile that will govern how the novel is written.\n\n"
            "Be specific and quantitative where possible. The profile should guide "
            "scene writers toward a consistent voice without being so rigid that every "
            "sentence sounds the same. Include banned phrases that are common AI writing tics."
        )
        style_context = [c for c in context.user_context if c.get("type") in ("style", "sample_writing")]
        if style_context:
            base += "\n\n## User-Provided Style References\n\n"
            for ctx in style_context:
                base += f"### {ctx.get('name', 'Reference')}\n{ctx.get('content', '')}\n\n"
        return base

    def _max_tokens(self) -> int:
        return 4096
