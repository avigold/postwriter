"""Prose vitality critic: evaluates the energy and craft of the writing itself."""

from postwriter.validation.base import register_soft_critic
from postwriter.validation.soft.base import BaseSoftCritic, ValidationContext


@register_soft_critic("prose_vitality")
class ProseVitalityCritic(BaseSoftCritic):
    dimension = "prose_vitality"
    system_prompt = (
        "You are a prose quality analyst for literary fiction. "
        "Evaluate the vitality and craft of the writing — not what it says, but how it says it. "
        "Good prose is specific, rhythmically varied, and avoids cliche. "
        "Great prose makes you stop and reread a sentence."
    )
    evaluation_prompt_template = (
        "Evaluate prose vitality:\n"
        "- Are verbs active and specific, or vague and passive?\n"
        "- Is there sentence length and rhythm variation?\n"
        "- Are images concrete and fresh, or generic?\n"
        "- Does the prose have energy, or does it feel dutiful and flat?\n"
        "- Are there any standout sentences or passages?\n"
        "- Are there cliches, dead metaphors, or filler phrases?\n"
        "- CRITICAL: Does the prose fall into self-referential observation patterns? "
        "For example: 'he registered this the way he registered most things', "
        "'a specific quality of feeling he had learned to keep off his face', "
        "'which was a thing he had learned to describe as intuitive'. "
        "This pattern — the narrator observing that the character is the kind of person "
        "who observes things — is a severe flaw. If it appears more than once, "
        "score below 0.5 regardless of other qualities.\n"
        "Score 0.0 = lifeless boilerplate. 1.0 = every sentence earns its place with precision and force."
    )

    def _extra_context(self, ctx: ValidationContext) -> str:
        sp = ctx.style_profile
        if sp.get("voice_description"):
            return f"\n## Target Voice\n{sp['voice_description']}"
        return ""
