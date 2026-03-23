"""Scene writer agent: generates prose from a scene brief, canon slice, and style profile."""

from __future__ import annotations

from typing import Any

from postwriter.agents.base import BaseAgent
from postwriter.agents.branch_profiles import BranchProfile
from postwriter.types import AgentContext, ModelTier


class SceneWriter(BaseAgent):
    """Generates scene prose. Returns raw text, not structured output."""

    role = "scene_writer"
    model_tier = ModelTier.SONNET
    template_name = "scene_writer.j2"
    response_model = None  # Returns prose, not structured data

    def __init__(self, *args: Any, branch_profile: BranchProfile | None = None, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._branch_profile = branch_profile

    def build_system_prompt(self, context: AgentContext) -> str:
        parts = [
            "You are a literary fiction writer. Write a single scene for a novel.",
            "",
            "CRITICAL RULES:",
            "- Write ONLY the scene prose. No meta-commentary, no notes, no headers.",
            "- Obey the POV constraint absolutely. Only narrate what the POV character can perceive.",
            "- Obey all prohibited moves listed in the scene brief.",
            "- Do not summarize the scene's meaning or theme. Dramatize, don't editorialize.",
            "- Do not use any banned phrases from the style profile.",
            "- Write with the emotional movement specified: the scene must TURN.",
        ]

        if self._branch_profile:
            parts.extend([
                "",
                f"STYLISTIC DIRECTION: {self._branch_profile.label}",
                self._branch_profile.writing_instructions,
            ])

        # Add style profile constraints
        if context.style_profile:
            sp = context.style_profile
            if sp.get("banned_phrases"):
                parts.append(f"\nBANNED PHRASES (never use these): {', '.join(sp['banned_phrases'])}")
            if sp.get("banned_moves"):
                parts.append(f"BANNED MOVES: {', '.join(sp['banned_moves'])}")
            if sp.get("voice_description"):
                parts.append(f"\nTARGET VOICE: {sp['voice_description']}")

        return "\n".join(parts)

    def build_template_context(self, context: AgentContext) -> dict[str, Any]:
        return {
            "scene_brief": context.scene_brief,
            "chapter_brief": context.chapter_brief,
            "characters": context.characters,
            "character_states": context.character_states,
            "preceding_scenes": context.preceding_scenes,
            "open_promises": context.open_promises,
            "style_profile": context.style_profile,
            "branch_profile": (
                {
                    "label": self._branch_profile.label,
                    "description": self._branch_profile.description,
                    "instructions": self._branch_profile.writing_instructions,
                }
                if self._branch_profile
                else None
            ),
        }

    def _max_tokens(self) -> int:
        return 8192

    def _temperature(self) -> float:
        return 1.0
